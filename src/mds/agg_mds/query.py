from fastapi import HTTPException, Path, Query, APIRouter, Request
from starlette.status import HTTP_404_NOT_FOUND
from mds import config, logger
from mds.agg_mds import datastore
from typing import Any, Dict, List
from pydantic import BaseModel
import redis
import threading
import asyncio
import time
from urllib.parse import urlparse
import json
from mds.agg_mds.commons import MDSInstance, ColumnsToFields, Commons, parse_config
from typing import Any, Optional
from pathlib import Path
from ..pub_sub import PubSubClient

mod = APIRouter()
url_parts = urlparse(config.ES_ENDPOINT)

def parse_config_from_file(path: Path) -> Optional[Commons]:
    if not path.exists():
        logger.error(f"configuration file: {path} does not exist")
        return None
    try:
        return parse_config(path.read_text())
    except IOError as ex:
        logger.error(f"cannot read configuration file {path}: {ex}")
        raise ex

commons = parse_config_from_file(Path("./agg_mds_config.json"))

agg_mds_subscription_pool = dict[str, threading.Thread]()

async def populate_metadata(name: str, common, results, use_temp_index=False):
    await datastore.init(hostname=url_parts.hostname, port=url_parts.port)
    mds_arr = [{k: v} for k, v in results.items()]

    total_items = len(mds_arr)

    if total_items == 0:
        logger.warning(f"populating {name} aborted as there are no items to add")
        return

    tags = {}

    # inject common_name field into each entry
    for x in mds_arr:
        key = next(iter(x.keys()))
        entry = next(iter(x.values()))

        def normalize(entry: dict) -> Any:
            # normalize study level metadata field names
            if common.study_data_field != config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD:
                entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD] = entry.pop(
                    common.study_data_field
                )
            # normalize variable level metadata field names, if available
            if (
                common.data_dict_field is not None
                and common.data_dict_field != config.AGG_MDS_DEFAULT_DATA_DICT_FIELD
            ):
                entry[config.AGG_MDS_DEFAULT_DATA_DICT_FIELD] = entry.pop(
                    common.data_dict_field
                )

            if (
                not hasattr(common, "columns_to_fields")
                or common.columns_to_fields is None
            ):
                return entry

            for column, field in common.columns_to_fields.items():
                if field == column:
                    continue
                if isinstance(field, ColumnsToFields):
                    entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD][
                        column
                    ] = field.get_value(entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD])
                else:
                    if field in entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD]:
                        entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD][column] = entry[
                            config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD
                        ][field]
            return entry

        entry = normalize(entry)

        # add the common field, selecting the name or an override (i.e. commons_name) and url to the entry

        entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD]["commons_name"] = (
            common.commons_name
            if hasattr(common, "commons_name") and common.commons_name is not None
            else name
        )

        # add to tags
        for t in entry[config.AGG_MDS_DEFAULT_STUDY_DATA_FIELD].get("tags") or {}:
            if "category" not in t:
                continue
            if t["category"] not in tags:
                tags[t["category"]] = set()
            if "name" in t:
                tags[t["category"]].add(t["name"])

    # process tags set to list
    for k, v in tags.items():
        tags[k] = list(tags[k])

    keys = list(results.keys())
    info = {"commons_url": common.commons_url}

    await datastore.update_metadata(name, mds_arr, keys, tags, info, use_temp_index)


@mod.get("/aggregate/join")
async def join_mesh(ip_address:str, hostname:str, channel_name:str):
    # Will this lead to memory leaks if I don't close threads properly?
    new_thread = threading.Thread(target=asyncio.run, args=(subscribe_to_commons(ip_address, hostname, channel_name),))
    new_thread.start()
    agg_mds_subscription_pool[hostname] = new_thread
    # need to do error checking here I think
    return "Mesh Joined"

@mod.get("/aggregate/status/{hostname}")
async def get_subscription_status(hostname: str):
    print(len(agg_mds_subscription_pool))
    print(agg_mds_subscription_pool)
    if hostname in agg_mds_subscription_pool:
        return agg_mds_subscription_pool[hostname].is_alive()
    else:
        return "Not Found"

async def subscribe_to_commons(ip_address:str, hostname:str, channel_name:str):
    # Setup connection to Redis
    # Gonna hard-code one ip address for now, will fix with config later
    # pubsub_client = PubSubClient()
    redis_client = redis.Redis(host=ip_address, port=6379, db=0)
    channel = channel_name

    # 2. Make redis spin
    # pubsub_client.subscribe(channel)
    print(f"Subscribed to {channel}. Waiting for messages...")
    last_index = 0
    while True:
        # print("trying to get message now")
        # message = redis_client.xrange(channel, last_index, "+", 1)
        message = redis_client.xread(streams={channel: last_index}, count=1)
        # print("got message")

        # print(f"message: {message}")
        
        # Check if there are any new entries. If not, wait and check again
        if len(message) == 0:
            time.sleep(1)
            continue

        print("Last: " + str(last_index))

        # time_index = message[0][0].decode('utf-8')
        # print(f"Got {time_index} entry")
        # read_data = message[0][1]
        # ms_time_index = time_index.split("-")[0]

        # increment last_index (is this okay? can I assume unique timestamps...)
        # last_index = str(int(ms_time_index) + 1) + "-0"
        last_index = message[0][1][-1][0]

        my_data = message[0][1]

        my_index = 'message'.encode('utf-8')
        content = my_data[0][1][my_index].decode('utf-8')

        message_array = content.split(" ", 2)
        rest_route = message_array[0]
        guid = message_array[1]
        data = message_array[2]
        # 3. Make switch statement to update ES according to redis updates
        # post
        if rest_route == "POST":
            # print(f"Getting https://{hostname}.dev.planx-pla.net/mds/metadata/{guid}?data=True")
            # print("Got data, doing thing now...")
            # print(data)

            # get the data
            results = {guid: {}}
            # response = httpx.get(f"https://{hostname}.dev.planx-pla.net/mds/metadata/{guid}?data=True")
            json_data = json.loads(data)
            results[guid].update(json_data)

            # print(len(json_data))

            # Add to ES
            # for name, common in commons.gen3_commons.items():
            for name, common in commons.adapter_commons.items():
                # print(common)
                # print(results)
                await populate_metadata(name, common, results, False)

        # put
        elif rest_route == "PUT":
            print("PUT not implemented")
            pass

        # delete
        elif rest_route == "DELETE":
            print("DELETE not implemented")
            pass

@mod.get("/aggregate/commons")
async def get_commons():
    """Returns a list of all commons with data in the aggregate metadata-service

    Example:

        { commons: ["commonsA", "commonsB" ] }

    """
    return await datastore.get_commons()


@mod.get("/aggregate/info/{what}")
async def get_commons_info(what: str):
    """Returns status and configuration information about aggregate metadata service.

    Return configuration information. Currently supports only 1 information type:
    **schema**

    Example:

    {
        "__manifest":{
            "type":"array",
            "properties":{
                "file_name":{
                    "type":"string",
                    "description":""
                },
                "file_size":{
                    "type":"integer",
                    "description":""
                }
            },
            "description":"",
            "default":[

            ]
        },
        "commons_url":{
            "type":"string",
            "description":""
        },
        ...
    }

    """
    res = await datastore.get_commons_attribute(what)
    if res:
        return res
    else:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            {"message": f"information for {what} not found", "code": 404},
        )


@mod.get("/aggregate/metadata")
async def get_aggregate_metadata(
    _: Request,
    limit: int = Query(
        20, description="Maximum number of records returned. (e.g. max: 2000)"
    ),
    offset: int = Query(0, description="Return results at this given offset."),
    counts: str = Query(
        "",
        description="Return count of a field instead of the value if field is an array\
           otherwise field is unchanged. If field is **null** will set field to **0**.\
           Multiple fields can be compressed by comma separating the field names:\
           **files,authors**",
    ),
    flatten: bool = Query(
        False, description="Return the results without grouping items by commons."
    ),
    pagination: bool = Query(
        False, description="If true will return a pagination object in the response"
    ),
):
    """Returns metadata records

    Returns medata records namespaced by commons as a JSON object.
    Example without pagination:

        {
          "commonA" : {
              ... Metadata
          },
           "commonB" : {
              ... Metadata
          }
          ...
        }

    The pagination option adds a pagination object to the response:

        {
            results: {
              "commonA" : {
                  ... Metadata
              },
               "commonB" : {
                  ... Metadata
              }
              ...
            },
            "pagination": {
                "hits": 64,
                "offset": 0,
                "pageSize": 20,
                "pages": 4
            }
        }

    The flatten option removes the commons' namespace so all results are a child or results:

        results: {
              ... Metadata from commons A
              ... Metadata from commons B
          }
          ...
        },


    The counts options when applied to an array or dictionary will replace
    the field value with its length. If the field values is None it will replace it with 0.
    All other types will be unchanged.
    """
    results = await datastore.get_all_metadata(limit, offset, counts, flatten)
    if pagination is False:
        return results.get("results", {})
    return results


@mod.get("/aggregate/metadata/{name}")
async def get_aggregate_metadata_for_commons(
    name: str = Path(
        description="Return the results without grouping items by commons."
    ),
):
    """et all metadata records from a commons by name

    Returns an array containing all the metadata entries for a single commons.
    There are no limit/offset parameters.

    Example:

        [
            {
                "gen3_discovery": {
                    "name": "bear",
                    "type": "study",
                    ...
                },
                "data_dictionaries": {
                    ...
                }
            },
            {
                "gen3_discovery": {
                    "name": "cat",
                    "type": "study",
                    ...
                }
            },
            ...
        ]

    """
    res = await datastore.get_all_named_commons_metadata(name)
    if res:
        return res
    else:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            {"message": f"no common exists with the given: {name}", "code": 404},
        )


@mod.get("/aggregate/tags")
async def get_aggregate_tags():
    """Returns aggregate category, name and counts across all commons

    Example:

            {
              "Data Type": {
                "total": 275,
                "names": [
                  {
                    "Genotype": 103,
                    "Clinical Phenotype": 100,
                    "DCC Harmonized": 24,
                    "WGS": 20,
                    "SNP/CNV Genotypes (NGS)": 6,
                    "RNA-Seq": 5,
                    "WXS": 5,
                    "Targeted-Capture": 3,
                    "miRNA-Seq": 3,
                    "CNV Genotypes": 2
                  }
                ]
              }
            }
    """
    res = await datastore.get_all_tags()
    if res:
        return res
    else:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            {"message": f"error retrieving tags from service", "code": 404},
        )


@mod.get("/aggregate/metadata/{name}/info")
async def get_aggregate_metadata_commons_info(name: str):
    """
    Returns information from the named commons.

    Example:

        { commons_url: "gen3.datacommons.io" }

    """
    res = await datastore.get_commons_attribute(name)
    if res:
        return res
    else:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            {"message": f"no common exists with the given: {name}", "code": 404},
        )


@mod.get("/aggregate/metadata/guid/{guid:path}")
async def get_aggregate_metadata_guid(guid: str):
    """Returns a metadata record by GUID

    Example:

         {
            "gen3_discovery": {
                "name": "cat",
                "type": "study",
                ...
            }
        }
    """
    res = await datastore.get_by_guid(guid)
    if res:
        return res
    else:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            {
                "message": f"no entry exists with the given guid: {guid}",
                "code": 404,
            },
        )


def init_app(app):
    if config.USE_AGG_MDS:
        app.include_router(mod, tags=["Aggregate"])

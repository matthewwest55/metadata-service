import redis
import time
import json
from src.mds.agg_mds import datastore, adapters
from src.mds import config, logger
import asyncio
from src.mds.agg_mds.commons import MDSInstance, ColumnsToFields, Commons, parse_config
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

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
url_parts = urlparse(config.ES_ENDPOINT)

last_index = 0

# Start with just getting the data from redis
redis_client = redis.Redis(host="34.173.90.136", port=6379, db=0, password="temporary_password")

download_time = 0.0
processing_time = 0.0
elastic_time = 0.0

while True:
	download_start = time.time()

	message = redis_client.xread(streams={"my_channel": last_index}, count=2000)

	download_end = time.time()

	download_time += download_end - download_start
	#print(download_time)

	if len(message) == 0:
		break

	# Now do the processing
	#print("Last: " + str(last_index))

	# time_index = message[0][0].decode('utf-8')
	# print(f"Got {time_index} entry")
	# read_data = message[0][1]
	# ms_time_index = time_index.split("-")[0]

	# increment last_index (is this okay? can I assume unique timestamps...)
	# last_index = str(int(ms_time_index) + 1) + "-0"
	last_index = message[0][1][-1][0]

	my_data = message[0][1]

	my_index = 'message'.encode('utf-8')
	results = {}
	processing_start = time.time()
	for i in range(0, len(my_data)):
	    content = my_data[i][1][my_index].decode('utf-8')

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
	        results[guid] = {}
	        # response = httpx.get(f"https://{hostname}.dev.planx-pla.net/mds/metadata/{guid}?data=True")
	        json_data = json.loads(data)
	        results[guid].update(json_data)

	        # print(len(json_data))
	processing_end = time.time()

	processing_time += processing_end - processing_start
	#print(processing_time)

	# print(results)

	# Now add it to elastic search
	async def populate_metadata(name: str, common, results, use_temp_index=False):
	    await datastore.init(hostname=url_parts.hostname, port=9200)
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

	    await datastore.update_metadata_bulk(name, mds_arr, keys, tags, info, use_temp_index)


	elastic_start = time.time()

	for name, common in commons.adapter_commons.items():
	    asyncio.run(populate_metadata(name, common, results, False))

	elastic_end = time.time()

	elastic_time += elastic_end - elastic_start
	#print(elastic_time)

print(download_time)
print(processing_time)
print(elastic_time)


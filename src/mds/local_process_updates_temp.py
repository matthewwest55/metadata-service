import asyncio
import httpx
from typing import Any, Optional
from mds import config, logger
from mds.agg_mds.commons import MDSInstance, ColumnsToFields, Commons, parse_config
from pathlib import Path
from mds.agg_mds import datastore

def parse_config_from_file(path: Path) -> Optional[Commons]:
    if not path.exists():
        logger.error(f"configuration file: {path} does not exist")
        return None
    try:
        return parse_config(path.read_text())
    except IOError as ex:
        logger.error(f"cannot read configuration file {path}: {ex}")
        raise ex

async def populate_metadata(name: str, common, results, use_temp_index=False):
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
        print("Entry: " + str(entry))

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

        print(entry)
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

    # print(name)
    # print(mds_arr)
    # print(keys)
    # print(tags)
    # print(info)
    # print(use_temp_index)

    await datastore.update_metadata(name, mds_arr, keys, tags, info, use_temp_index)

commons = parse_config_from_file(Path("./agg_mds_config.json"))

print(commons)

guid = "1000_Genomes_Project"

async def do_work():
    results = {}
    response = httpx.get(f"https://gen3.datacommons.io/mds/metadata/{guid}?data=True")
    json_data = response.json()
    results.update(json_data)

    print(results)

    for name, common in commons.gen3_commons.items():
        print(common)
        print(results)
        await populate_metadata(name, common, results, False)

asyncio.run(do_work())
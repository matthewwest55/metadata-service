from src.mds.agg_mds import datastore, adapters
from src.mds import config, logger
import asyncio
from src.mds.agg_mds.commons import MDSInstance, ColumnsToFields, Commons, parse_config
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

url_parts = urlparse(config.ES_ENDPOINT)

async def test():
    await datastore.init(hostname=url_parts.hostname, port=9200)
    count = await datastore.get_count()
    print(count)

asyncio.run(test())

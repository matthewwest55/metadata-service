import json
import re
import redis

from asyncpg import UniqueViolationError
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import bindparam
from sqlalchemy.dialects.postgresql import insert
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from .admin_login import admin_required
from .models import db, Metadata
from . import config
from .objects import FORBIDDEN_IDS
from .pub_sub import *

mod = APIRouter()
print("getting client")
pub_sub_client = PubSubClient()
print("got client")
channel = 'my_channel'

@mod.post("/metadata")
async def batch_create_metadata(
    request: Request, data_list: list[dict], overwrite: bool = True
):
    """Create metadata in batch."""
    request.scope.get("add_close_watcher", lambda: None)()
    created = []
    updated = []
    conflict = []
    bad_input = []
    authz = json.loads(config.DEFAULT_AUTHZ_STR)
    async with db.acquire() as conn:
        if overwrite:
            data = bindparam("data")
            stmt = await conn.prepare(
                insert(Metadata)
                .values(guid=bindparam("guid"), data=data, authz=authz)
                .on_conflict_do_update(
                    index_elements=[Metadata.guid], set_=dict(data=data)
                )
                .returning(db.text("xmax"))
            )
            for data in data_list:
                if data["guid"] in FORBIDDEN_IDS:
                    bad_input.append(data["guid"])
                elif await stmt.scalar(data) == 0:
                    created.append(data["guid"])
                else:
                    updated.append(data["guid"])
        else:
            stmt = await conn.prepare(
                insert(Metadata).values(
                    guid=bindparam("guid"), data=bindparam("data"), authz=authz
                )
            )
            for data in data_list:
                if data["guid"] in FORBIDDEN_IDS:
                    bad_input.append(data["guid"])
                else:
                    try:
                        await stmt.status(data)
                    except UniqueViolationError:
                        conflict.append(data["guid"])
                    else:
                        created.append(data["guid"])
    # Check if we created any new keys
    if created:
        for created_metadata_guid in created:
            pub_sub_client.publish(channel, "POST " + str(created_metadata_guid))
    return dict(
        created=created, updated=updated, conflict=conflict, bad_input=bad_input
    )


@mod.post("/metadata/{guid:path}")
async def create_metadata(guid, data: dict, overwrite: bool = False):
    """Create metadata for the GUID."""
    created = True
    authz = json.loads(config.DEFAULT_AUTHZ_STR)

    # GUID should not be in the FORBIDDEN_ID list (eg, 'upload').
    # This will help avoid conflicts between
    # POST /api/v1/objects/{GUID or ALIAS} and POST /api/v1/objects/upload endpoints
    if guid in FORBIDDEN_IDS:
        raise HTTPException(
            HTTP_400_BAD_REQUEST, "GUID cannot have value: {FORBIDDEN_IDS}"
        )

    if overwrite:
        rv = await db.first(
            insert(Metadata)
            .values(guid=guid, data=data, authz=authz)
            .on_conflict_do_update(index_elements=[Metadata.guid], set_=dict(data=data))
            .returning(Metadata.data, db.text("xmax"))
        )
        if rv["xmax"] != 0:
            created = False
    else:
        try:
            rv = (
                await Metadata.insert()
                .values(guid=guid, data=data, authz=authz)
                .returning(*Metadata)
                .gino.first()
            )
        except UniqueViolationError:
            raise HTTPException(HTTP_409_CONFLICT, f"Conflict: {guid}")
    if created:
        pass
        # pub_sub_client.publish(channel, "testingPOST-GUID")
        # pub_sub_client.publish(channel, "POST " + str(guid) + " " + json.dumps(data))
        # return JSONResponse(rv["data"], HTTP_201_CREATED)
    else:
        return rv["data"]


@mod.put("/metadata/{guid:path}")
async def update_metadata(guid, data: dict, merge: bool = False):
    """Update the metadata of the GUID.

    If `merge` is True, then any top-level keys that are not in the new data will be
    kept, and those that also exist in the new data will be replaced completely. This
    is also known as the shallow merge. The metadata service currently doesn't support
    deep merge.
    """
    # TODO PUT should create if it doesn't exist...
    metadata = (
        await Metadata.update.values(data=(Metadata.data + data) if merge else data)
        .where(Metadata.guid == guid)
        .returning(*Metadata)
        .gino.first()
    )
    if metadata:
        pub_sub_client.publish(channel, "PUT " + str(guid))
        return metadata.data
    else:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Not found: {guid}")


@mod.delete("/metadata/{guid:path}")
async def delete_metadata(guid):
    """Delete the metadata of the GUID."""
    metadata = (
        await Metadata.delete.where(Metadata.guid == guid)
        .returning(*Metadata)
        .gino.first()
    )
    if metadata:
        pub_sub_client.publish(channel, "DELETE " + str(guid))
        return metadata.data
    else:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Not found: {guid}")


# This should be made into a post request with a better endpoint, I'll deal with that later
# Might this also go into its own file? 
@mod.get("/publish")
async def publish_metadata(request: Request):
    """Publish the metadata currently in the database."""
    
    queries = {}
    for key, value in request.query_params.multi_items():
        if key not in {"data", "limit", "offset"}:
            queries.setdefault(key, []).append(value)

    def add_filter(query):
        for path, values in queries.items():
            if "*" in values:
                # query all records with a value for this path
                path = list(path.split("."))
                field = path.pop()
                query = query.where(Metadata.data[path].has_key(field))
            else:
                values = ["*" if v == "\*" else v for v in values]
                if "." in path:
                    path = list(path.split("."))
                query = query.where(
                    db.or_(Metadata.data[path].astext == v for v in values)
                )

        # TODO/FIXME: There's no updated date on the records, and without that
        # this "pagination" is prone to produce inconsistent results if someone is
        # trying to paginate using offset WHILE data is being added
        #
        # The only real way to try and reduce that risk
        # is to order by updated date (so newly added stuff is
        # at the end and new records don't end up in a page earlier on)
        # This is how our indexing service handles this situation.
        #
        # But until we have an updated_date, we can't do that, so naively order by
        # GUID for now and accept this inconsistency risk.
        query = query.order_by(Metadata.guid)

        return query

    all_metadata = await add_filter(Metadata.query).gino.all()

    # all_metadata = await Metadata.query.gino.all()

    # print(all_metadata)

    # okay, need to just iterate over all the metadata that is in the store and publish it
    # LEFT-OFF: want to put this inside an async function so we don't block
    await pub_sub_client.batch_publish(channel, all_metadata)

    return(len(all_metadata))

def init_app(app):
    app.include_router(mod, tags=["Maintain"], dependencies=[Depends(admin_required)])

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.entity import Entity
from graphrag.query.input.retrieval.entities import (
    get_entity_by_id,
    get_entity_by_key,
)


def test_get_entity_by_id():
    assert (
        get_entity_by_id(
            {
                entity.id: entity
                for entity in [
                    Entity(
                        id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
                        short_id="sid1",
                        title="title1",
                    ),
                ]
            },
            "00000000-0000-0000-0000-000000000000",
        )
        is None
    )

    assert get_entity_by_id(
        {
            entity.id: entity
            for entity in [
                Entity(
                    id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
                    short_id="sid1",
                    title="title1",
                ),
                Entity(
                    id="c4f93564-4507-4ee4-b102-98add401a965",
                    short_id="sid2",
                    title="title2",
                ),
                Entity(
                    id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
                    short_id="sid3",
                    title="title3",
                ),
            ]
        },
        "7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
    ) == Entity(
        id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9", short_id="sid3", title="title3"
    )

    assert get_entity_by_id(
        {
            entity.id: entity
            for entity in [
                Entity(
                    id="2da37c7a50a844d4aa2cfd401e19976c",
                    short_id="sid1",
                    title="title1",
                ),
                Entity(
                    id="c4f9356445074ee4b10298add401a965",
                    short_id="sid2",
                    title="title2",
                ),
                Entity(
                    id="7c6f2bc947c9445393a3d2e174a02cd9",
                    short_id="sid3",
                    title="title3",
                ),
            ]
        },
        "7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
    ) == Entity(id="7c6f2bc947c9445393a3d2e174a02cd9", short_id="sid3", title="title3")

    assert get_entity_by_id(
        {
            entity.id: entity
            for entity in [
                Entity(id="id1", short_id="sid1", title="title1"),
                Entity(id="id2", short_id="sid2", title="title2"),
                Entity(id="id3", short_id="sid3", title="title3"),
            ]
        },
        "id3",
    ) == Entity(id="id3", short_id="sid3", title="title3")


def test_get_entity_by_key():
    assert (
        get_entity_by_key(
            [
                Entity(
                    id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
                    short_id="sid1",
                    title="title1",
                ),
            ],
            "id",
            "00000000-0000-0000-0000-000000000000",
        )
        is None
    )

    assert get_entity_by_key(
        [
            Entity(
                id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
                short_id="sid1",
                title="title1",
            ),
            Entity(
                id="c4f93564-4507-4ee4-b102-98add401a965",
                short_id="sid2",
                title="title2",
            ),
            Entity(
                id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
                short_id="sid3",
                title="title3",
            ),
        ],
        "id",
        "7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
    ) == Entity(
        id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9", short_id="sid3", title="title3"
    )

    assert get_entity_by_key(
        [
            Entity(
                id="2da37c7a50a844d4aa2cfd401e19976c", short_id="sid1", title="title1"
            ),
            Entity(
                id="c4f9356445074ee4b10298add401a965", short_id="sid2", title="title2"
            ),
            Entity(
                id="7c6f2bc947c9445393a3d2e174a02cd9", short_id="sid3", title="title3"
            ),
        ],
        "id",
        "7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
    ) == Entity(id="7c6f2bc947c9445393a3d2e174a02cd9", short_id="sid3", title="title3")

    assert get_entity_by_key(
        [
            Entity(id="id1", short_id="sid1", title="title1"),
            Entity(id="id2", short_id="sid2", title="title2"),
            Entity(id="id3", short_id="sid3", title="title3"),
        ],
        "id",
        "id3",
    ) == Entity(id="id3", short_id="sid3", title="title3")

    assert get_entity_by_key(
        [
            Entity(id="id1", short_id="sid1", title="title1", rank=1),
            Entity(id="id2", short_id="sid2", title="title2a", rank=2),
            Entity(id="id3", short_id="sid3", title="title3", rank=3),
            Entity(id="id2", short_id="sid2", title="title2b", rank=2),
        ],
        "rank",
        2,
    ) == Entity(id="id2", short_id="sid2", title="title2a", rank=2)

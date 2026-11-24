
from unittest.mock import AsyncMock, Mock

import pytest

from src.AgentDefinitions.Context import (
    AgentContext,
    create_execution_context,
)


@pytest.mark.asyncio
async def test_graphql_execution_context():
    schema = Mock()
    schema.execute = AsyncMock(return_value={"data": "ok"})

    execute_gql = create_execution_context(schema)

    result = await execute_gql(
        "query Test { __typename }",
        {"id": "123"},
    )

    assert result == {"data": "ok"}
    schema.execute.assert_awaited_once_with(
        "query Test { __typename }",
        variable_values={"id": "123"},
    )


def test_agent_context_defaults():
    ctx = AgentContext()

    assert ctx.subgraph_name == "demo"
    assert ctx.executor is None
    assert ctx.user_id is None
    assert ctx.authorization_token is None

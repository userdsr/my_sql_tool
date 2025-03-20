from collections.abc import Generator
from typing import Any
import records
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from sqlalchemy.exc import SQLAlchemyError

class MySqlToolTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_uri = tool_parameters.get("db_uri") or self.runtime.credentials.get("db_uri")
        user_password = tool_parameters.get("db_password") or self.runtime.credentials.get("db_password")
        if user_password:
            db_uri = db_uri.replace("@", f":{user_password}@")
            db_uri = db_uri.replace("mysql", "mysql+pymysql")
        db = records.Database(db_uri)
        query = tool_parameters.get("query").strip()
        format = tool_parameters.get("format", "json")

        if query.lower().startswith('select') or query.lower().startswith('desc') or query.lower().startswith('describe'):
            try:
                rows = db.query(query)
                if format == 'json':
                    result = rows.as_dict()
                    for r in result:
                        yield self.create_json_message(r)
                elif format == 'md':
                    result = str(rows.dataset)
                    yield self.create_text_message(result)
                elif format == 'csv':
                    result = rows.export('csv').encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/csv', 'filename': 'result.csv'})
                elif format == 'yaml':
                    result = rows.export('yaml').encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/yaml', 'filename': 'result.yaml'})
                elif format == 'xlsx':
                    result = rows.export('xlsx')
                    yield self.create_blob_message(result, meta={
                        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','filename': 'result.xlsx'})
                elif format == 'html':
                    result = rows.export('html').encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/html', 'filename': 'result.html'})
                else:
                    raise ValueError(f"Unsupported format: {format}")
            except SQLAlchemyError as e:
                error_msg = f"查询语句存在语法错误，请检查语句！错误原因：{str(e)}"
                if format == 'json':
                    result = {"error": error_msg}
                    yield self.create_json_message(result)
                elif format == 'md':
                    result = f"Error: {error_msg}"
                    yield self.create_text_message(result)
                elif format == 'csv':
                    result = f"Error: {error_msg}".encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/csv', 'filename': 'result.csv'})
                elif format == 'yaml':
                    result = f"Error: {error_msg}".encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/yaml', 'filename': 'result.yaml'})
                elif format == 'xlsx':
                    result = f"Error: {error_msg}"
                    result = result.encode()
                    yield self.create_blob_message(result, meta={
                        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    })
                elif format == 'html':
                    result = f"Error: {error_msg}".encode()
                    yield self.create_blob_message(result, meta={'mime_type': 'text/html', 'filename': 'result.html'})
                else:
                    raise ValueError(f"Unsupported format: {format}")
        else:
                yield self.create_text_message(f"Error: 目前仅支持SELECT和DESC语句！")
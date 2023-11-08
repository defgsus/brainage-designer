from bad.server.handlers import JsonBaseHandler, DbRestHandler
from bad.modules import ModuleFactory
from bad.modules.analysis import AnalysisSourceModule
from bad.plugins.analysis.reduction import AnalysisReduction


class AnalysisSourcePreviewHandler(JsonBaseHandler):

    def post(self, uuid):
        data = self.json_body
        limit = 1000

        try:
            module: AnalysisSourceModule = ModuleFactory.new_module(
                name=AnalysisSourceModule.name,
                parameters=data["parameter_values"],
            )

            reduction = AnalysisReduction([module])
            reduction.init(limit_files=limit)

            table = None
            try:
                if module.get_parameter_value("table_file"):
                    rows = module.open_table_file()
                    table = {
                        "headers": list(rows[0]) if rows else [],
                        "rows": rows,
                    }
            except Exception as e:
                table = {
                    "error": f"{type(e).__name__}: {e}"
                }

        except Exception as e:
            self.write({"error": f"{type(e).__name__}: {e}"})
            self.set_status(400)
            return

        self.write({
            "files": reduction.files,
            "attributes": reduction.attribute_names,
            "limit": limit,
            "table": table,
        })

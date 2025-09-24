from frappe import _

def get_data():
    return [
        {
            "module_name": "Dev Assistant",
            "color": "blue",
            "icon": "fa fa-cog",
            "type": "module",
            "label": _("Dev Assistant"),
            "description": _("Universal Data Sync and Development Tools")
        }
    ]
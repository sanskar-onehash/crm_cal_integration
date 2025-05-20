frappe.listview_settings["Cal Event Type"] = {
  refresh: function (listview) {
    console.log(listview);
    addFetchEventTypesButton(listview);
  },
};

function addFetchEventTypesButton(listview) {
  const BTN_LABEL = "Fetch Event Types";
  listview.page.remove_inner_button(BTN_LABEL);
  listview.page.add_inner_button(
    BTN_LABEL,
    async () => {
      const data = await frappe.call({
        method: "crm_cal_integration.api.pull_cal_event_types",
      });
    },
    null,
    "primary",
  );
}

function onEdit(e) {
  handleAuditEdit(e);
}

// Compatibility entrypoint for legacy triggers named myFunction.
function myFunction(e) {
  handleAuditEdit(e);
}

function handleAuditEdit(e) {
  try {
    if (!e || !e.range) return;

    var sourceSheet = e.range.getSheet();
    var sourceSpreadsheet = sourceSheet.getParent();
    var sourceSheetName = sourceSheet.getName();

    // Do not log edits made in the audit worksheet itself.
    if (sourceSheetName === "audit_log") return;

    var userEmail = "";
    try {
      userEmail = Session.getActiveUser().getEmail() || "unknown";
    } catch (err) {
      userEmail = "unknown";
    }

    var oldValue = typeof e.oldValue === "undefined" ? "" : String(e.oldValue);
    var newValue = typeof e.value === "undefined" ? "" : String(e.value);

    var auditSheet = sourceSpreadsheet.getSheetByName("audit_log");
    if (!auditSheet) {
      auditSheet = sourceSpreadsheet.insertSheet("audit_log");
      auditSheet.appendRow([
        "time",
        "actor",
        "action",
        "sheet_name",
        "cell_a1",
        "old_value",
        "new_value",
      ]);
    }

    auditSheet.appendRow([
      new Date().toISOString(),
      userEmail,
      "edit",
      sourceSheetName,
      e.range.getA1Notation(),
      oldValue,
      newValue,
    ]);
  } catch (error) {
    // Keep silent to avoid user-facing interruption in sheet edits.
  }
}

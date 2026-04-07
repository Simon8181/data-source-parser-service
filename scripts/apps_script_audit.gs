var AUDIT_TAB = "audit_ew";

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

    if (sourceSheetName === AUDIT_TAB) return;

    // EWid: display value in column E on the edited row.
    var ewId = String(
      sourceSheet.getRange(e.range.getRow(), 5).getDisplayValue() || ""
    );

    var auditSheet = sourceSpreadsheet.getSheetByName(AUDIT_TAB);
    if (!auditSheet) {
      auditSheet = sourceSpreadsheet.insertSheet(AUDIT_TAB);
      auditSheet.appendRow(["time", "ew_id"]);
    }

    auditSheet.appendRow([new Date().toISOString(), ewId]);
  } catch (error) {
    // Keep silent to avoid user-facing interruption in sheet edits.
  }
}

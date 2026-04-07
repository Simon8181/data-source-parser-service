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

    // EWid: display value in column C on the edited row (same as getDisplayValue in audit sheet).
    var ewId = String(
      sourceSheet.getRange(e.range.getRow(), 3).getDisplayValue() || ""
    );
    if (!ewId.trim()) return;

    var auditSheet = sourceSpreadsheet.getSheetByName(AUDIT_TAB);
    if (!auditSheet) {
      auditSheet = sourceSpreadsheet.insertSheet(AUDIT_TAB);
      auditSheet.appendRow(["audit_id", "time", "ew_id"]);
    }

    var auditId = Utilities.getUuid();
    var nowIso = new Date().toISOString();

    // Upsert by ew_id: same EWid => update audit_id + time only; no new row.
    var lastRow = auditSheet.getLastRow();
    if (lastRow <= 1) {
      auditSheet.appendRow([auditId, nowIso, ewId]);
      return;
    }

    var matchRow = -1;
    for (var r = 2; r <= lastRow; r++) {
      var existing = String(
        auditSheet.getRange(r, 3).getDisplayValue() || ""
      );
      if (existing === ewId) {
        matchRow = r;
        break;
      }
    }

    if (matchRow > 0) {
      // (row, col, numRows, numColumns) — exactly one row, cols A:B
      auditSheet.getRange(matchRow, 1, 1, 2).setValues([[auditId, nowIso]]);
    } else {
      auditSheet.appendRow([auditId, nowIso, ewId]);
    }
  } catch (error) {
    // Keep silent to avoid user-facing interruption in sheet edits.
  }
}

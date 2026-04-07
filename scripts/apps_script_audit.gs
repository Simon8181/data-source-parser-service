/**
 * When any of the first four worksheets (left-to-right tab order) is edited,
 * writes the same UTC timestamp (text) into column AZ for every row touched.
 * Column AZ = 52 (A=1 … Z=26, AA=27 … AZ=52).
 */

var FIRST_SHEET_COUNT = 4;
var COL_AZ = 52;
/** IANA timezone for UTC (Apps Script accepts GMT for formatDate). */
var TZ_UTC = "GMT";

function onEdit(e) {
  handleFirstFourSheetAzTimestamp(e);
}

// Compatibility entrypoint for legacy triggers named myFunction.
function myFunction(e) {
  handleFirstFourSheetAzTimestamp(e);
}

function handleFirstFourSheetAzTimestamp(e) {
  try {
    if (!e || !e.range) return;

    var sh = e.range.getSheet();
    var ss = sh.getParent();
    var sheets = ss.getSheets();
    var idx = sheetIndex_(sheets, sh);
    if (idx < 0 || idx >= FIRST_SHEET_COUNT) return;

    var startRow = e.range.getRow();
    var numRows = e.range.getNumRows();
    if (numRows < 1) return;

    var now = new Date();
    var utcStamp =
      Utilities.formatDate(now, TZ_UTC, "yyyy-MM-dd'T'HH:mm:ss") + "Z";
    var values = [];
    for (var i = 0; i < numRows; i++) {
      values.push([utcStamp]);
    }

    var azRange = sh.getRange(startRow, COL_AZ, numRows, 1);
    azRange.setValues(values);
  } catch (error) {
    // Keep silent to avoid user-facing interruption in sheet edits.
  }
}

function sheetIndex_(sheets, target) {
  var id = target.getSheetId();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId() === id) return i;
  }
  return -1;
}

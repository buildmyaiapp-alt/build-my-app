// ============================================================
// GOOGLE APPS SCRIPT — Paste this in script.google.com
// Handles: Google Sheet + Email + WhatsApp confirmation
// ============================================================

// ── CONFIG — Fill these in ──────────────────────────────────
const CONFIG = {
  SHEET_NAME:      'Leads',                          // Tab name in your Google Sheet
  SENDER_NAME:     'Palash — AI App Workshop',       // Your name in emails
  WORKSHOP_DATE:   'Will be announced on WhatsApp',  // Or put real date
  WHATSAPP_API_KEY: '',    // Fill after getting Interakt/WATI key (leave blank for now)
  WHATSAPP_NUMBER:  '',    // Your Interakt sender number (leave blank for now)
};
// ────────────────────────────────────────────────────────────

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const { name, email, phone, paymentId, amount } = data;

    // 1️⃣ SAVE TO GOOGLE SHEET
    saveLead(name, email, phone, paymentId, amount);

    // 2️⃣ SEND CONFIRMATION EMAIL
    sendEmail(name, email, paymentId);

    // 3️⃣ SEND WHATSAPP MESSAGE (when API key is ready)
    if (CONFIG.WHATSAPP_API_KEY) {
      sendWhatsApp(name, phone);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ success: true, message: 'Lead saved!' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ── ALLOW CORS for static site — also saves leads via image pixel ──
function doGet(e) {
  try {
    const p = e.parameter;
    if (p && p.name && p.email) {
      // Save lead from image pixel fired before/after payment
      saveLead(p.name, p.email, p.phone || '', p.paymentId || 'LEAD', null);
      // Send confirmation email only when payment confirmed
      if (p.paymentId && p.paymentId !== 'LEAD' && p.paymentId !== 'PAYMENT_INITIATED') {
        sendEmail(p.name, p.email, p.paymentId);
      }
    }
  } catch(err) {
    Logger.log('doGet error: ' + err.message);
  }
  return ContentService
    .createTextOutput(JSON.stringify({ status: 'OK' }))
    .setMimeType(ContentService.MimeType.JSON);
}

// ────────────────────────────────────────────────────────────
// 1. SAVE LEAD TO GOOGLE SHEET
// ────────────────────────────────────────────────────────────
function saveLead(name, email, phone, paymentId, amount) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  // Create sheet + headers if first time
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
    sheet.appendRow([
      '📅 Date & Time',
      '👤 Name',
      '📧 Email',
      '📱 WhatsApp',
      '💳 Payment ID',
      '💰 Amount',
      '✅ Status',
      '📝 Notes'
    ]);
    // Style header row
    const header = sheet.getRange(1, 1, 1, 8);
    header.setBackground('#0d1b6e');
    header.setFontColor('#ffffff');
    header.setFontWeight('bold');
    header.setFontSize(11);
    sheet.setFrozenRows(1);
    // Column widths
    sheet.setColumnWidth(1, 180);
    sheet.setColumnWidth(2, 150);
    sheet.setColumnWidth(3, 220);
    sheet.setColumnWidth(4, 140);
    sheet.setColumnWidth(5, 220);
    sheet.setColumnWidth(6, 100);
    sheet.setColumnWidth(7, 100);
    sheet.setColumnWidth(8, 200);
  }

  // Add lead row
  const row = [
    new Date(),
    name,
    email,
    phone,
    paymentId || 'TEST',
    amount ? '₹' + (amount / 100) : '₹249',
    '✅ Paid',
    'New lead — contact on WhatsApp'
  ];
  sheet.appendRow(row);

  // Highlight new row in light yellow
  const lastRow = sheet.getLastRow();
  sheet.getRange(lastRow, 1, 1, 8).setBackground('#fffde7');
}

// ────────────────────────────────────────────────────────────
// 2. SEND CONFIRMATION EMAIL
// ────────────────────────────────────────────────────────────
function sendEmail(name, email, paymentId) {
  const subject = '🎉 Payment Confirmed — Your Workshop Seat is Secured!';

  const htmlBody = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
    <style>
      body{margin:0;padding:0;background:#f4f4f4;font-family:'Helvetica Neue',Arial,sans-serif;}
      .wrap{max-width:560px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);}
      .header{background:linear-gradient(135deg,#0d1b6e,#1a237e);padding:36px 32px;text-align:center;}
      .header h1{color:#fff;font-size:26px;font-weight:900;margin:0 0 6px;}
      .header p{color:rgba(255,255,255,.75);font-size:14px;margin:0;}
      .tick{font-size:56px;margin-bottom:12px;}
      .body{padding:32px;}
      .greeting{font-size:20px;font-weight:800;color:#0d1b6e;margin-bottom:8px;}
      .msg{font-size:15px;color:#555;line-height:1.7;margin-bottom:24px;}
      .badge{background:#fff9c4;border:2px solid #f9d300;border-radius:10px;padding:16px 20px;margin-bottom:24px;text-align:center;}
      .badge .amount{font-size:28px;font-weight:900;color:#0d1b6e;}
      .badge .label{font-size:13px;color:#777;margin-top:4px;}
      .steps{background:#f8f9ff;border-radius:12px;padding:20px;margin-bottom:24px;}
      .steps h3{font-size:13px;font-weight:800;color:#0d1b6e;text-transform:uppercase;letter-spacing:1px;margin:0 0 14px;}
      .step{display:flex;align-items:flex-start;gap:12px;margin-bottom:12px;}
      .step:last-child{margin-bottom:0;}
      .step-num{min-width:26px;height:26px;border-radius:50%;background:#0d1b6e;color:#fff;font-size:12px;font-weight:900;display:flex;align-items:center;justify-content:center;}
      .step-text{font-size:14px;color:#333;line-height:1.5;padding-top:3px;}
      .payment-id{background:#f5f5f5;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:13px;color:#555;margin-bottom:24px;}
      .cta{display:block;background:#25d366;color:#fff;text-decoration:none;text-align:center;padding:16px;border-radius:50px;font-size:16px;font-weight:800;margin-bottom:20px;}
      .footer{background:#f8f8f8;border-top:1px solid #eee;padding:20px 32px;text-align:center;}
      .footer p{font-size:12px;color:#aaa;margin:0;line-height:1.6;}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="header">
        <div class="tick">🎉</div>
        <h1>Payment Confirmed!</h1>
        <p>AI App Building Workshop — Your seat is secured</p>
      </div>
      <div class="body">
        <div class="greeting">Hey ${name}! 👋</div>
        <p class="msg">
          You're officially in! Your payment has been received and your seat for the
          <strong>AI App Building Workshop</strong> is confirmed.
          <br/><br/>
          In this workshop, you'll build your own professional app in just 30 minutes —
          no coding, no developer, no lakh rupees needed.
        </p>

        <div class="badge">
          <div class="amount">₹249 Paid ✅</div>
          <div class="label">Payment ID: ${paymentId || 'TEST_MODE'}</div>
        </div>

        <div class="steps">
          <h3>📋 What Happens Next</h3>
          <div class="step">
            <div class="step-num">1</div>
            <div class="step-text"><strong>Our team will contact you on WhatsApp</strong> within 24 hours with the workshop details and joining link.</div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div class="step-text"><strong>Check this email inbox</strong> — we'll send you the workshop schedule and preparation guide.</div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div class="step-text"><strong>Show up on workshop day</strong> — build your app live in 30 minutes and get your first client! 🚀</div>
          </div>
        </div>

        <p style="font-size:14px;color:#777;margin-bottom:8px;">Your Payment Reference:</p>
        <div class="payment-id">Payment ID: ${paymentId || 'TEST_MODE'}</div>

        <p style="font-size:14px;color:#555;margin-bottom:16px;">
          Any questions? Simply reply to this email or WhatsApp us directly.
        </p>
      </div>
      <div class="footer">
        <p>
          © AI App Building Workshop by Palash<br/>
          This email was sent because you purchased a seat for the workshop.<br/>
          <span style="color:#e8251a;">100% Money Back Guarantee</span> if you're not satisfied.
        </p>
      </div>
    </div>
  </body>
  </html>
  `;

  GmailApp.sendEmail(email, subject, '', {
    htmlBody: htmlBody,
    name: CONFIG.SENDER_NAME,
    replyTo: Session.getActiveUser().getEmail()
  });
}

// ────────────────────────────────────────────────────────────
// 3. SEND WHATSAPP MESSAGE (via Interakt API)
// Fill WHATSAPP_API_KEY in CONFIG above after signup at interakt.ai
// ────────────────────────────────────────────────────────────
function sendWhatsApp(name, phone) {
  const cleanPhone = phone.replace(/\D/g, '');

  const payload = {
    "countryCode": "+91",
    "phoneNumber": cleanPhone,
    "callbackData": "workshop_confirmation",
    "type": "Template",
    "template": {
      "name": "workshop_confirmation",
      "languageCode": "en",
      "bodyValues": [name, "AI App Building Workshop", "₹249", "30 minutes"]
    }
  };

  const options = {
    method: 'post',
    headers: {
      'Authorization': 'Basic ' + CONFIG.WHATSAPP_API_KEY,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch('https://api.interakt.ai/v1/public/message/', options);
    Logger.log('WhatsApp sent: ' + response.getContentText());
  } catch (err) {
    Logger.log('WhatsApp error: ' + err.message);
  }
}

// ============================================================
// GOOGLE APPS SCRIPT — Paste this in script.google.com
// Handles: Google Sheet + Email + WhatsApp confirmation
// ============================================================

// ── CONFIG — Fill these in ──────────────────────────────────
const CONFIG = {
  SHEET_NAME:      'Batch 2',
  SENDER_NAME:     'Palash — AI App Workshop',
  WORKSHOP_DATE:   '17th May 2026, 2:00 PM IST',
  WHATSAPP_API_KEY: '',
  WHATSAPP_NUMBER:  '',
};
// ────────────────────────────────────────────────────────────

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const { name, email, phone, paymentId, amount } = data;
    saveLead(name, email, phone, paymentId, amount);
    if (paymentId && paymentId !== 'PAYMENT_INITIATED' && paymentId !== 'LEAD') {
      sendEmail(name, email, paymentId);
      if (CONFIG.WHATSAPP_API_KEY) sendWhatsApp(name, phone);
    }
    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  try {
    const p = (e && e.parameter) ? e.parameter : {};
    if (p && p.name && p.email) {
      const isPaid = p.paymentId && p.paymentId !== 'LEAD' && p.paymentId !== 'PAYMENT_INITIATED';

      if (isPaid) {
        // Try to update existing row first (avoid duplicates)
        const updated = updateLeadStatus(p.phone || p.email, p.paymentId);
        if (!updated) {
          // No existing row found — add new paid row
          saveLead(p.name, p.email, p.phone || '', p.paymentId, 9900);
        }
        // Send confirmation email
        sendEmail(p.name, p.email, p.paymentId);
        if (CONFIG.WHATSAPP_API_KEY) sendWhatsApp(p.name, p.phone);
      } else {
        // Just initiated — save as Initiated (not Paid)
        saveLead(p.name, p.email, p.phone || '', 'INITIATED', null);
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
  const ss = SpreadsheetApp.openById('18c0VazYcBZtgdFDzJK6baFb4ZQieb0_mhfWzzkIcKRA');
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
    sheet.appendRow([
      '📅 Date & Time', '👤 Name', '📧 Email',
      '📱 WhatsApp', '💳 Payment ID', '💰 Amount',
      '✅ Status', '📝 Notes'
    ]);
    const header = sheet.getRange(1, 1, 1, 8);
    header.setBackground('#0d1b6e');
    header.setFontColor('#ffffff');
    header.setFontWeight('bold');
    header.setFontSize(11);
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 180); sheet.setColumnWidth(2, 150);
    sheet.setColumnWidth(3, 220); sheet.setColumnWidth(4, 140);
    sheet.setColumnWidth(5, 220); sheet.setColumnWidth(6, 100);
    sheet.setColumnWidth(7, 120); sheet.setColumnWidth(8, 200);
  }

  // Determine status based on paymentId
  const isPaid = paymentId && paymentId !== 'INITIATED' && paymentId !== 'PAYMENT_INITIATED' && paymentId !== 'LEAD';
  const status = isPaid ? '✅ Paid' : '🔄 Initiated';
  const bgColor = isPaid ? '#e8f5e9' : '#fff9c4'; // green for paid, yellow for initiated

  const row = [
    new Date(),
    name,
    email,
    phone,
    paymentId || 'INITIATED',
    amount ? '₹' + (amount / 100) : (isPaid ? '₹99' : '—'),
    status,
    isPaid ? 'Payment confirmed ✅' : 'Form filled — awaiting payment'
  ];
  sheet.appendRow(row);

  const lastRow = sheet.getLastRow();
  sheet.getRange(lastRow, 1, 1, 8).setBackground(bgColor);
}

// ────────────────────────────────────────────────────────────
// 2. UPDATE EXISTING ROW FROM INITIATED → PAID
// ────────────────────────────────────────────────────────────
function updateLeadStatus(phoneOrEmail, paymentId) {
  const ss = SpreadsheetApp.openById('18c0VazYcBZtgdFDzJK6baFb4ZQieb0_mhfWzzkIcKRA');
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) return false;

  const data = sheet.getDataRange().getValues();
  // Search from bottom (most recent) — columns: 0=date,1=name,2=email,3=phone,4=paymentId,5=amount,6=status
  for (let i = data.length - 1; i >= 1; i--) {
    const rowPhone = String(data[i][3]);
    const rowEmail = String(data[i][2]);
    const rowStatus = String(data[i][6]);

    if (rowPhone.includes(phoneOrEmail) || rowEmail === phoneOrEmail) {
      // Already paid — return true to prevent duplicate entry
      if (rowStatus.includes('Paid')) return true;
      // Still initiated — update to Paid
      if (rowStatus.includes('Initiated')) {
        sheet.getRange(i + 1, 5).setValue(paymentId);       // Payment ID
        sheet.getRange(i + 1, 6).setValue('₹99');            // Amount
        sheet.getRange(i + 1, 7).setValue('✅ Paid');         // Status
        sheet.getRange(i + 1, 8).setValue('Payment confirmed ✅');
        sheet.getRange(i + 1, 1, 1, 8).setBackground('#e8f5e9'); // Green
        return true;
      }
    }
  }
  return false;
}

// ────────────────────────────────────────────────────────────
// 3. SEND CONFIRMATION EMAIL
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
      .badge{background:#e8f5e9;border:2px solid #4CAF50;border-radius:10px;padding:16px 20px;margin-bottom:24px;text-align:center;}
      .badge .amount{font-size:28px;font-weight:900;color:#0d1b6e;}
      .badge .label{font-size:13px;color:#777;margin-top:4px;}
      .steps{background:#f8f9ff;border-radius:12px;padding:20px;margin-bottom:24px;}
      .steps h3{font-size:13px;font-weight:800;color:#0d1b6e;text-transform:uppercase;letter-spacing:1px;margin:0 0 14px;}
      .step{display:flex;align-items:flex-start;gap:12px;margin-bottom:12px;}
      .step:last-child{margin-bottom:0;}
      .step-num{min-width:26px;height:26px;border-radius:50%;background:#0d1b6e;color:#fff;font-size:12px;font-weight:900;display:flex;align-items:center;justify-content:center;}
      .step-text{font-size:14px;color:#333;line-height:1.5;padding-top:3px;}
      .payment-id{background:#f5f5f5;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:13px;color:#555;margin-bottom:24px;}
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
          <div class="amount">₹99 Paid ✅</div>
          <div class="label">Payment ID: ${paymentId || 'CONFIRMED'}</div>
        </div>
        <div class="steps">
          <h3>📋 What Happens Next</h3>
          <div class="step">
            <div class="step-num">1</div>
            <div class="step-text"><strong>Join our WhatsApp group</strong> to get the Zoom link for the workshop.</div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div class="step-text"><strong>Workshop date:</strong> ${CONFIG.WORKSHOP_DATE} — Live on Zoom.</div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div class="step-text"><strong>Show up and build your app</strong> in 30 minutes — no coding needed! 🚀</div>
          </div>
        </div>
        <p style="font-size:14px;color:#777;margin-bottom:8px;">Your Payment Reference:</p>
        <div class="payment-id">Payment ID: ${paymentId || 'CONFIRMED'}</div>
        <p style="font-size:14px;color:#555;margin-bottom:16px;">
          Any questions? WhatsApp us at +91 91096 37004
        </p>
      </div>
      <div class="footer">
        <p>
          © AI App Building Workshop by Palash<br/>
          110% Money Back Guarantee if you can't build your app in 30 minutes.
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
// 4. SEND WHATSAPP MESSAGE (via Interakt API)
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
      "bodyValues": [name, "AI App Building Workshop", "₹99", "30 minutes"]
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
    UrlFetchApp.fetch('https://api.interakt.ai/v1/public/message/', options);
  } catch (err) {
    Logger.log('WhatsApp error: ' + err.message);
  }
}

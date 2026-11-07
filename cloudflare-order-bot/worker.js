const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };
const ADMIN_USERNAME = "iman_1258";
const STATE_TTL = 60 * 60 * 24;
const ORDER_TTL = 60 * 60 * 24 * 30;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}
function keyboard(rows) {
  return { inline_keyboard: rows };
}
async function tg(env, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${method}`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!data.ok) throw new Error(data.description || "Telegram API error");
  return data.result;
}
async function say(env, chatId, text, reply_markup) {
  return tg(env, "sendMessage", {
    chat_id: chatId,
    text,
    ...(reply_markup ? { reply_markup } : {}),
    disable_web_page_preview: true,
  });
}
async function answerCallback(env, id, text = "") {
  return tg(env, "answerCallbackQuery", { callback_query_id: id, text });
}
async function getState(env, chatId) {
  return (await env.ORDERS.get(`state:${chatId}`, "json")) || null;
}
async function setState(env, chatId, state) {
  await env.ORDERS.put(`state:${chatId}`, JSON.stringify(state), { expirationTtl: STATE_TTL });
}
async function clearState(env, chatId) {
  await env.ORDERS.delete(`state:${chatId}`);
}
function clean(value, max = 500) {
  return String(value || "").trim().replace(/[<>]/g, "").slice(0, max);
}
async function start(env, chat) {
  const user = chat.from || {};
  if ((user.username || "").toLowerCase() === ADMIN_USERNAME) {
    await env.ORDERS.put("admin_chat_id", String(chat.id));
    await say(env, chat.id, "پنل مدیریت NEOVO فعال شد. از این پس درخواست‌های سفارش به همین حساب ارسال می‌شوند.");
  }
  await say(
    env,
    chat.id,
    "سلام! به سامانه سفارش طراحی سایت NEOVO خوش آمدید.\n\nبرای ثبت سفارش، مراحل کوتاهی را طی می‌کنید. اطلاعات تماس فقط برای پیگیری همین درخواست استفاده می‌شود و حداکثر تا ۳۰ روز نگهداری خواهد شد. لطفاً اطلاعات حساس یا رمز عبور ارسال نکنید.",
    keyboard([[{ text: "🌐 ثبت سفارش طراحی سایت", callback_data: "order:start" }]])
  );
}
async function beginOrder(env, chatId) {
  await setState(env, chatId, { step: "name", order: {} });
  await say(env, chatId, "۱ از ۶ — نام و نام خانوادگی‌تان را بنویسید. (برای لغو /cancel)");
}
async function promptSiteType(env, chatId) {
  await setState(env, chatId, { step: "site_type", order: (await getState(env, chatId)).order });
  await say(env, chatId, "۳ از ۶ — چه نوع وب‌سایتی می‌خواهید؟", keyboard([
    [{ text: "فروشگاهی", callback_data: "type:فروشگاهی" }, { text: "شرکتی", callback_data: "type:شرکتی" }],
    [{ text: "شخصی / نمونه‌کار", callback_data: "type:شخصی و نمونه‌کار" }, { text: "وبلاگ / آموزشی", callback_data: "type:وبلاگ و آموزشی" }],
    [{ text: "سایر", callback_data: "type:سایر" }],
  ]));
}
async function showReview(env, chatId, order) {
  const summary =
    "۶ از ۶ — بررسی نهایی سفارش\n\n" +
    `نام: ${order.name}\nکسب‌وکار: ${order.business}\nنوع سایت: ${order.site_type}\nامکانات: ${order.features}\nراه ارتباطی: ${order.contact}\n\n` +
    "با ثبت نهایی، موافقت می‌کنید اطلاعات بالا برای پیگیری سفارش در اختیار مدیر NEOVO قرار گیرد.";
  await setState(env, chatId, { step: "confirm", order });
  await say(env, chatId, summary, keyboard([
    [{ text: "✅ ثبت نهایی سفارش", callback_data: "order:submit" }],
    [{ text: "❌ لغو سفارش", callback_data: "order:cancel" }],
  ]));
}
async function handleCallback(env, query) {
  const chatId = query.message.chat.id;
  const data = query.data || "";
  await answerCallback(env, query.id);
  if (data === "order:start") return beginOrder(env, chatId);
  if (data === "order:cancel") {
    await clearState(env, chatId);
    return say(env, chatId, "درخواست ثبت سفارش لغو شد. هر زمان خواستید می‌توانید دوباره شروع کنید.",
      keyboard([[{ text: "🌐 ثبت سفارش طراحی سایت", callback_data: "order:start" }]]));
  }
  if (data.startsWith("type:")) {
    const state = await getState(env, chatId);
    if (!state || state.step !== "site_type") return say(env, chatId, "این مرحله منقضی شده است؛ دوباره شروع کنید.");
    state.order.site_type = clean(data.slice(5), 80);
    state.step = "features";
    await setState(env, chatId, state);
    return say(env, chatId, "۴ از ۶ — چه امکاناتی لازم دارید؟ مثلاً درگاه پرداخت، سبد خرید، معرفی خدمات، فرم تماس یا پنل مدیریت را بنویسید.");
  }
  if (data === "order:submit") {
    const state = await getState(env, chatId);
    if (!state || state.step !== "confirm") return say(env, chatId, "سفارش آماده ثبت نیست؛ لطفاً دوباره شروع کنید.");
    const orderId = crypto.randomUUID().slice(0, 8).toUpperCase();
    const order = {
      id: orderId,
      ...state.order,
      telegram_user: query.from.username ? "@" + query.from.username : "ندارد",
      created_at: new Date().toISOString(),
      status: "new",
    };
    await env.ORDERS.put(`order:${orderId}`, JSON.stringify(order), { expirationTtl: ORDER_TTL });
    await clearState(env, chatId);
    const adminId = await env.ORDERS.get("admin_chat_id");
    if (adminId) {
      const adminText =
        `🆕 سفارش جدید NEOVO — #${orderId}\n\nنام: ${order.name}\nکسب‌وکار: ${order.business}\nنوع سایت: ${order.site_type}\nامکانات: ${order.features}\nراه ارتباطی: ${order.contact}\nآیدی تلگرام مشتری: ${order.telegram_user}\n\nبرای پیگیری، به مشتری از طریق راه ارتباطی ثبت‌شده پیام بدهید.`;
      await say(env, adminId, adminText);
    }
    return say(env, chatId,
      `✅ سفارش شما با موفقیت ثبت شد.\nکد پیگیری: #${orderId}\n\n${adminId ? "درخواست برای مدیر ارسال شد." : "درخواست ذخیره شد. مدیر باید ابتدا ربات را با حساب @iman_1258 باز و Start کند تا اعلان‌ها فعال شوند."}`,
      keyboard([[{ text: "ثبت سفارش دیگر", callback_data: "order:start" }]])
    );
  }
}
async function handleMessage(env, message) {
  const chatId = message.chat.id;
  const text = clean(message.text, 1000);
  if (text === "/start") return start(env, message);
  if (text === "/cancel") {
    await clearState(env, chatId);
    return say(env, chatId, "فرآیند سفارش لغو شد.");
  }
  if (text === "/help") return say(env, chatId, "برای ثبت سفارش روی دکمه «ثبت سفارش طراحی سایت» بزنید. برای لغو هر مرحله /cancel را ارسال کنید.");
  const state = await getState(env, chatId);
  if (!state) return say(env, chatId, "برای شروع ثبت سفارش، /start را بزنید.");
  if (!text) return say(env, chatId, "لطفاً پاسخ را به صورت متن ارسال کنید.");
  if (state.step === "name") {
    state.order.name = text.slice(0, 100);
    state.step = "business";
    await setState(env, chatId, state);
    return say(env, chatId, "۲ از ۶ — نام کسب‌وکار یا حوزه فعالیتتان چیست؟ اگر هنوز کسب‌وکاری ندارید، بنویسید «شخصی».");
  }
  if (state.step === "business") {
    state.order.business = text.slice(0, 160);
    await setState(env, chatId, state);
    return promptSiteType(env, chatId);
  }
  if (state.step === "features") {
    state.order.features = text.slice(0, 500);
    state.step = "contact";
    await setState(env, chatId, state);
    return say(env, chatId, "۵ از ۶ — راه ارتباطی دلخواهتان را بنویسید؛ مثلاً آیدی تلگرام یا شماره کاری. فقط اطلاعاتی را بفرستید که با اشتراک‌گذاری آن موافقید.");
  }
  if (state.step === "contact") {
    state.order.contact = text.slice(0, 160);
    return showReview(env, chatId, state.order);
  }
  if (state.step === "confirm") return say(env, chatId, "برای ثبت، دکمه «ثبت نهایی سفارش» را بزنید یا /cancel را ارسال کنید.");
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return json({ ok: true, service: "NEOVO order bot" });
    if (url.pathname === "/register" && request.method === "POST") {
      if (!env.SETUP_KEY || request.headers.get("authorization") !== `Bearer ${env.SETUP_KEY}`) {
        return json({ ok: false, error: "Unauthorized" }, 401);
      }
      const webhookUrl = `${url.origin}/telegram`;
      const result = await tg(env, "setWebhook", {
        url: webhookUrl,
        secret_token: env.WEBHOOK_SECRET,
        allowed_updates: ["message", "callback_query"],
        drop_pending_updates: true,
      });
      return json({ ok: true, webhook: webhookUrl, telegram: result });
    }
    if (url.pathname !== "/telegram" || request.method !== "POST") return json({ ok: false }, 404);
    if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
      return json({ ok: false, error: "Unauthorized" }, 401);
    }
    let update;
    try { update = await request.json(); } catch { return json({ ok: false }, 400); }
    try {
      if (update.callback_query) await handleCallback(env, update.callback_query);
      else if (update.message) await handleMessage(env, update.message);
      return json({ ok: true });
    } catch (error) {
      console.error("Update handling failed", error);
      if (update.message?.chat?.id) {
        try { await say(env, update.message.chat.id, "مشکلی پیش آمد. لطفاً دوباره تلاش کنید یا /start را بزنید."); } catch {}
      }
      return json({ ok: true });
    }
  },
};

# NEOVO Order Bot (Cloudflare Worker)

این سرویس، ثبت سفارش طراحی سایت را داخل ربات تلگرام انجام می‌دهد. سفارش‌ها در Cloudflare KV با مهلت نگهداری ۳۰ روز ذخیره می‌شوند. کدها و اطلاعات مشتریان را در GitHub قرار ندهید.

## راه‌اندازی

1. در Cloudflare یک KV Namespace با نام دلخواه بسازید.
2. مقدار Namespace ID را در `wrangler.toml` جایگزین `REPLACE_WITH_KV_NAMESPACE_ID` کنید.
3. از پوشه `cloudflare-order-bot` دستورهای زیر را اجرا کنید:

```bash
npm install -g wrangler
wrangler login
wrangler secret put TELEGRAM_TOKEN
wrangler secret put WEBHOOK_SECRET
wrangler secret put SETUP_KEY
wrangler deploy
```

- `TELEGRAM_TOKEN`: همان توکن ربات؛ آن را در چت یا GitHub ننویسید.
- `WEBHOOK_SECRET`: یک رشته تصادفی ۲۰ تا ۶۰ کاراکتری شامل حروف و اعداد.
- `SETUP_KEY`: یک کلید تصادفی محرمانه برای راه‌اندازی webhook.

4. پس از Deploy، آدرس Worker را بردارید و ثبت webhook را با این درخواست انجام دهید (آدرس و کلید را جایگزین کنید):

```bash
curl -X POST "https://YOUR-WORKER.workers.dev/register" -H "Authorization: Bearer YOUR_SETUP_KEY"
```

5. در تلگرام، با حسابی که نام کاربری آن `@iman_1258` است وارد ربات شوید و Start را بزنید. این کار شناسه گفت‌وگوی مدیر را برای دریافت اعلان سفارش ثبت می‌کند.

## جریان سفارش

- مشتری /start را می‌زند و «ثبت سفارش طراحی سایت» را انتخاب می‌کند.
- نام، حوزه فعالیت، نوع سایت، امکانات و راه ارتباطی را وارد می‌کند.
- قبل از ثبت، خلاصه را بررسی و صریحاً تأیید می‌کند.
- درخواست در KV ذخیره و برای مدیر ارسال می‌شود.
- کاربر می‌تواند در هر مرحله با `/cancel` فرآیند را لغو کند.

## نکات مهم

- این Worker از همان Telegram bot token استفاده می‌کند و با ارسال‌های زمان‌بندی‌شده GitHub Actions تداخل polling ندارد.
- مدیر باید یک بار خودش ربات را Start کند تا بتواند پیام مستقیم دریافت کند.
- سفارش‌ها پس از ۳۰ روز منقضی می‌شوند.
- این نسخه فقط سفارش را دریافت و اعلان می‌کند؛ پرداخت آنلاین، قیمت‌گذاری و پنل مدیریت در آن وجود ندارد.

# 🚀 AWS S3 Static Website Deployment Guide

This tutorial walks through deploying a static website using **Amazon S3** and **CloudFront**, with optional support for a **custom domain and HTTPS**. Perfect for portfolio sites or lightweight web projects.

---

## 📁 Step 1: Create the S3 Bucket

1. Go to S3 → Create bucket.
2. Name your bucket (e.g., `your-site-name`) — leave all other settings default.
3. In the **Properties** tab:
   - Scroll to **Static website hosting**
   - Click **Edit**
   - Enable **Static website hosting**
   - Set `index.html` as the home page
   - Optionally set `error.html` for error documents

---

## 🌐 Step 2: Create CloudFront Distribution

1. Go to CloudFront → **Distributions** → **Create Distribution**
2. In the **Origin** settings:
   - Click **Browse S3**
   - Select the bucket you just created
   - Click **Next**
3. In **Distribution Settings**:
   - Set a custom domain (CNAME) if using a custom domain
   - *(Note: You’ll need to update DNS records later if using a custom domain)*

---

## 🔒 Step 3: Configure Origin Access Control (OAC)

1. Go to the **Origins** tab in your distribution
2. Select your origin → Click **Edit**
3. Scroll to **Origin access control settings**
   - Ensure **Origin access** is set to *Origin access control settings*
   - If no OAC is selected, create a new one
4. Copy the policy provided

---

## 📜 Step 4: Set S3 Permissions

1. Go to **S3** → your bucket → **Permissions** tab
2. Edit the **Bucket Policy**
3. Paste the policy copied from CloudFront
4. Save
5. Make sure **Block all public access** is turned **ON**

---

## 🕒 Step 5: Wait for CloudFront

- CloudFront deployment may take **10–15 minutes**
- Once done, access your site via the CloudFront domain (e.g., `https://d1234.cloudfront.net`)

---

## 🌍 (Optional) Step 6: Custom Domain with HTTPS

1. Go to CloudFront → your distribution → **Settings**
2. Click **Add a domain**
3. Enter your domain name
4. Select the existing certificate or request a new wildcard certificate
5. Use the provided CNAME values to create a new CNAME record on your DNS providers website
6. Validate → Add domain → Wait for propagation

Once completed, your static site will be accessible via your custom domain using **HTTPS**.

---

## ✅ Final Result

You now have a scalable, secure, and fast static website hosted entirely on AWS infrastructure — ideal for portfolios, documentation, or landing pages.

---

## 🛠 Tools Used

- Amazon S3
- Amazon CloudFront
- AWS Certificate Manager
- Cloudflare (optional, for DNS)

---

## 📬 Questions?

Feel free to [contact me](mailto:westbrook.jww@gmail.com) or connect via [GitHub](https://github.com/westbrookjw).
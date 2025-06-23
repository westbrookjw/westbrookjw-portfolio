Create AWS account.
View all services → Select S3 → Create bucket.
Name the bucket (e.g., your-site-name) → leave the rest as default unless you need versioning or encryption.
Go to the bucket’s “Properties” tab.
Scroll to “Static website hosting”
Enable it
Specify index.html as the home page
Optionally set error.html for error documents
Go to CloudFront → Distributions → Create Distribution.
In the Origin settings:
Choose “Browse S3”
Select the bucket you just created
Click “Next”
In the Distribution Settings:
Leave most defaults
Optionally set a custom domain (CNAME) if you have one
Note: If using a domain, you’ll later need to update DNS records in your DNS provider (e.g. Cloudflare)
Once the distribution is created, go to “Origins and Origin Groups” tab
Select your origin
Click “Edit”
Scroll to “Origin access control settings”
Ensure Origin access control (OAC) is enabled
Copy the S3 bucket policy snippet provided
Go back to S3 → Your bucket → Permissions tab
Click “Bucket policy”
Paste the policy you copied from CloudFront
Save
In S3 Permissions, ensure Block all public access is OFF.
In the Bucket Policy, make sure it allows only CloudFront (via the OAC) to access the content.
Wait for CloudFront to deploy (~10-15 min).
Access the distribution’s domain name (e.g., d1234.cloudfront.net) to verify your static website is working.
(Optional) Set up a custom domain with HTTPS:
In Route 53 or Cloudflare, point your domain to your CloudFront distribution using a CNAME
Add the custom domain in your CloudFront settings
Request a free certificate in AWS Certificate Manager
Attach the certificate to your distribution
Deploy changes and wait for propagation
Leave all as is and click "Copy policy".













Solid State by HTML5 UP
html5up.net | @ajlkn
Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)

Credits:

	Demo Images:
		Unsplash (unsplash.com)

	Icons:
		Font Awesome (fontawesome.io)

	Other:
		jQuery (jquery.com)
		Scrollex (github.com/ajlkn/jquery.scrollex)
		Responsive Tools (github.com/ajlkn/responsive-tools)

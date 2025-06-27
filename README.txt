This is a tutorial on how to create an AWS S3 static website

Create S3 Bucket
Name the bucket (e.g., your-site-name) → leave the rest as default
Go to the bucket’s “Properties” tab.
Scroll to “Static website hosting” and select "edit"
Enable "Static website hosting"
Specify index.html as the home page

Optionally set error.html for error documents
Go to CloudFront → Distributions → Create Distribution:
	In the Origin settings:
		Choose “Browse S3”
		Select the bucket you just created
		Click “Next”
Go to Distribution Settings:
	Set a custom domain (CNAME) if you have one
	Note: If using a domain, you’ll later need to update DNS records in your DNS provider (e.g. Cloudflare)
Go to “Origins” tab
Select your origin
Click “Edit”
Scroll to “Origin access control settings”
Ensure "Origin access" is set to: Origin access control settings
Under "Origin access control" ensure that an OAC has been selecte - If not create one

Copy the policy provided
Go back to S3 → Your bucket → Permissions tab
Edit “Bucket policy”
Paste the policy you copied from CloudFront
Save
In S3 Permissions, ensure "Block all public access" is ON.
Wait for CloudFront to deploy (~10-15 min).
Access the distribution’s domain name (e.g., d1234.cloudfront.net) to verify your static website is working.

(Optional) Set up a custom domain with HTTPS:
Go to Certificate Manager
Request
Request a public certificate
In "Domain names" enter the FQDN or multiple (Ex: example.com & www.example.com)
Keep the rest as default and press "request"

It should now take you to the new certificate's page. If not go to Certificate Manager → Certificates → "Your Certificate"
Under "Domains" copy the CNAME name & value
Now create a new CNAME record with the name & value with your DNS provider
After a few minutes your certificate should be issued

Go to CloudFront → Distributions → <your distribution>
Under "settings" press "Add a domain"
Enter the domain that you would like
If you don't have certificate to import, select "create a wildcard certificate" to have once created in AWS (Certificate Manager)
Once done, you will be provided with a CNAME name & value
Use this info to create a new CNAME entry with your DNS provider
Now click Validate and your certificate should be issued
Then press "Next" then "Add domains"
Give it a few minutes to update and you should now be able to access your S3 static website via the provided domain name

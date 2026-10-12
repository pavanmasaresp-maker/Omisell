"""Public pages (login ke bina): Privacy Policy aur Account Delete. Play Store in dono ke URL maangta hai."""
import os

from django.http import HttpResponse

CONTACT = os.environ.get("SUPPORT_EMAIL") or os.environ.get("ADMIN_EMAIL") or "support@example.com"

STYLE = ("body{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:20px;line-height:1.55;"
         "color:#1b1b1b}h1{font-size:1.5rem}h2{font-size:1.1rem;margin-top:1.6rem}")


def page(title, body):
    html = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title>"
            f"<style>{STYLE}</style></head><body><h1>{title}</h1>{body}</body></html>")
    return HttpResponse(html)


def privacy(request):
    return page("OmniSell Privacy Policy", f"""
<p>Last updated: 2026. OmniSell helps sellers manage products, stock and orders across online marketplaces.</p>
<h2>What we collect</h2>
<ul><li>Your email address and name (from Google or email sign-in).</li>
<li>Business data you enter: products, SKUs, stock, orders and customer name / phone / city for those orders.</li>
<li>Marketplace connection details you provide (store address and API token). Tokens are stored encrypted.</li></ul>
<h2>How we use it</h2>
<p>Only to run the app for you: show your data, sync stock and orders with the marketplaces you connect, and keep you signed in.
We do not sell your data and do not show ads.</p>
<h2>Sharing</h2>
<p>Data is sent only to the marketplaces you connect, and to our infrastructure providers (hosting, database, Firebase
Authentication) who process it for us.</p>
<h2>Your data is yours</h2>
<p>You can delete your account and all its data any time from the app (More &rarr; Delete account) or see
<a href='/account-delete'>how to delete your account</a>.</p>
<h2>Security</h2>
<p>Data is transferred over HTTPS and every seller's data is kept separate from other sellers.</p>
<h2>Contact</h2><p>{CONTACT}</p>""")


def account_delete(request):
    return page("Delete your OmniSell account", f"""
<p>You can delete your account and all its data yourself:</p>
<ol><li>Open the OmniSell app and sign in.</li><li>Go to <b>More</b> &rarr; <b>Delete account</b>.</li>
<li>Type DELETE and confirm.</li></ol>
<p>This removes your products, stock, orders, marketplace connections and login permanently.
If you cannot access the app, email <b>{CONTACT}</b> from your registered email address and we will delete it for you.</p>""")

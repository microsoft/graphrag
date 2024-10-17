function onConsentChanged(categoryPreferences) {
	console.log("onConsentChanged", categoryPreferences);        
}


cb = document.createElement("div");
cb.id = "cookie-banner";
document.body.insertBefore(cb, document.body.children[0]);

window.WcpConsent && WcpConsent.init("en-US", "cookie-banner", function (err, consent) {
	if (!err) {
		console.log("consent: ", consent);
		window.manageConsent = () => consent.manageConsent();
		siteConsent = consent;          
	} else {
		console.log("Error initializing WcpConsent: "+ err);
	}
}, onConsentChanged, WcpConsent.themes.light);
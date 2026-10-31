import jenkins.model.Jenkins
import jenkins.model.JenkinsLocationConfiguration
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy

def instance = Jenkins.get()
def password = System.getenv('JENKINS_ADMIN_PASSWORD')

JenkinsLocationConfiguration.get().setUrl(System.getenv('JENKINS_URL') ?: 'http://localhost:8080/')
JenkinsLocationConfiguration.get().save()
println '[init] Jenkins URL configured'

if (password) {
    def realm = new HudsonPrivateSecurityRealm(false)
    if (realm.getUser('admin') == null) {
        realm.createAccount('admin', password)
    }
    instance.setSecurityRealm(realm)

    def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
    strategy.setAllowAnonymousRead(false)
    instance.setAuthorizationStrategy(strategy)
    instance.save()
    println '[init] admin account and authorization strategy configured'
}

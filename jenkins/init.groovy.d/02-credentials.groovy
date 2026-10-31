import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import hudson.util.Secret
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl

def store = SystemCredentialsProvider.getInstance().getStore()
def existing = store.getCredentials(Domain.global()).collect { it.id }

def keyFile = new File('/run/secrets/deploy_key')
if (keyFile.exists() && !existing.contains('github-deploy-readonly')) {
    def source = new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(keyFile.getText('UTF-8'))
    store.addCredentials(Domain.global(), new BasicSSHUserPrivateKey(
        CredentialsScope.GLOBAL,
        'github-deploy-readonly',
        'git',
        source,
        '',
        'GitHub read-only deploy key'
    ))
    println '[init] SSH deploy key credential created'
}

def webhookSecret = System.getenv('JENKINS_WEBHOOK_SECRET')
if (webhookSecret && !existing.contains('github-webhook-secret')) {
    store.addCredentials(Domain.global(), new StringCredentialsImpl(
        CredentialsScope.GLOBAL,
        'github-webhook-secret',
        'GitHub webhook secret (never committed)',
        Secret.fromString(webhookSecret)
    ))
    println '[init] webhook secret credential created'
}

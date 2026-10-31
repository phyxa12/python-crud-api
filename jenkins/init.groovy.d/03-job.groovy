import jenkins.model.Jenkins

def instance = Jenkins.get()
def jobName = System.getenv('JENKINS_JOB_NAME') ?: 'python-crud-api-pipeline'

if (instance.getItem(jobName) == null) {
    def xml = new File('/run/config/job.xml').getText('UTF-8')
    instance.createProjectFromXML(jobName, new ByteArrayInputStream(xml.getBytes('UTF-8')))
    println "[init] job ${jobName} created"
} else {
    println "[init] job ${jobName} already exists"
}

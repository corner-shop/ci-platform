import groovy.json.JsonSlurper
import java.util.regex.*

def jenkinsGitCredential = 'JENKINS CREDENTIALS'
def jenkinsJobDslFileName = 'jenkins.jobs.dsl'
def stashUrl = 'https://bitbucket.acme.com/'
def matchBranchesRegex = 'FILL_ME_IN_WITH_A_REGEX_THAT_MATCHES_BRANCHES'
def matchProjectsRegex = 'FILL_ME_IN_WITH_A_REGEX_THAT_MATCHES_PROJECTS'


def projectsApi = new URL("${stashUrl}/rest/api/1.0/projects")
def projects = new JsonSlurper().parse(projectsApi.newReader())

projects.get("values").each {
    def stashProjectKey = it.get("key")

    if (stashProjectKey) {

        println "INFO - Searching for repos in project $stashProjectKey"

        def reposApi = new URL("${stashUrl}/rest/api/1.0/projects/${stashProjectKey}/repos")
        def repos = new JsonSlurper().parse(reposApi.newReader())

        if (repos) {
            def repoList = repos.get("values")

            println "INFO - Found ${repoList.size} repos for project ${stashProjectKey}."

            repoList.each { repo ->
                if (repo.get("slug") ==~ "${matchProjectsRegex}") {
                    processRepo(repo, stashProjectKey, jenkinsGitCredential, jenkinsJobDslFileName)
                }
            }
        }
    }
}

private void processRepo(repo, stashProjectKey, jenkinsGitCredential, jenkinsJobDslFileName) {
    def repoSlug = repo.get("slug")

    if (repoSlug) {

        println "INFO - Searching for branches in repo $repoSlug"

        def branchApi = new URL("${stashUrl}/rest/api/1.0/projects/${stashProjectKey}/repos/${repoSlug}/branches")
        def branches = new JsonSlurper().parse(branchApi.newReader())

        branches.get("values").each { branch ->
            if (branch.get("displayId") ==~ "${matchBranchesRegex}") {
                processBranch(jenkinsGitCredential, branch, stashProjectKey, repoSlug, jenkinsJobDslFileName)
            }
        }
    }
}

private void processBranch(jenkinsGitCredential, branch, stashProjectKey, repoSlug, jenkinsJobDslFileName) {
    def branchName = branch.get("displayId")
    def branchSimpleName = branchName.replace("/", "-")
    def jobDslUrl = new URL("${stashUrl}/rest/api/1.0/projects/${stashProjectKey}/repos/${repoSlug}/browse/${jenkinsJobDslFileName}?raw&at=${branchName}")

    println "INFO - Found branch ${repoSlug} - ${branchName}"
    println "INFO - Looking for job dsl ${jobDslUrl}"

    def urlConnection = (HttpURLConnection) jobDslUrl.openConnection()
    def status = urlConnection.getResponseCode()
    def repoAndBranchName = "${repoSlug} - ${branchName}"

    if (status == 200) {
        println "INFO - Found job dsl for " + repoAndBranchName

        def dslJson = new JsonSlurper().parse(jobDslUrl.newReader())

        if (dslJson.get("lines") != null) {
            try {
                println "INFO - Executing job dsl for $repoAndBranchName"

                Binding binding = getJobDslBinding(
                        stashProjectKey,
                        repoSlug,
                        branchSimpleName,
                        branchName,
                        jenkinsGitCredential)

                executeJobDsl(binding, dslJson)
            } catch (Exception e) {
                println "ERROR - Couldn't run job dsl for ${repoAndBranchName}: ${e.getMessage()} \n ${e.printStackTrace()}"
            }
        }

    } else {
        println "WARN - No jenkins job dsl found for $repoAndBranchName"
    }
}

private void executeJobDsl(Binding binding, dslJson) {
    def jobDsl = [];

    dslJson.get("lines").each {
        jobDsl.add(it.text)
    }

    def jobDslString = jobDsl.join("\n")

    GroovyShell shell = new GroovyShell(binding);
    Object value = shell.parse(jobDslString);

    job value.run()
}

private Binding getJobDslBinding(stashProjectKey, repoSlug, branchSimpleName, branchName, jenkinsGitCredential) {
    Binding binding = new Binding();

    binding.setVariable('stashProjectKey', stashProjectKey)
    binding.setVariable('projectName', repoSlug)
    binding.setVariable('branchSimpleName', branchSimpleName)
    binding.setVariable('branchName', branchName)
    binding.setVariable('jenkinsGitCredential', jenkinsGitCredential)

    binding
}
Closure job = {
    // Job Name
    name "${stashProjectKey}-${projectName}-${branchSimpleName}"

    // Where should jenkins run the job
    label ('master')

    // Where should Jenkins get the source code from
    scm {
        git {
            remote {
                url ("<STASH URL>/git/${stashProjectKey}/${projectName}.git")
                branch (branchName)
                credentials (jenkinsGitCredential)
            }
        }

    }

    // How often should the job run
    triggers {
        scm ('H/10 * * * *')
    }

    // Gradle build steps to execute
    steps {
        def gradleTask = '<GRADLE BUILD STEPS>'
        gradle (gradleTask, null, true) {
            def makeExecutable = it / 'makeExecutable'
            makeExecutable.setValue (true)
        }
    }

    // Additional Report Settings
    publishers {
        jacocoCodeCoverage  {
            minimumLineCoverage '60'
            maximumLineCoverage '90'
            execPattern '**/build/**/*.exec'
        }

        archiveJunit ("**/build/test-results/*.xml", true, true)
    }

}
return job
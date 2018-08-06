from celery.task import task, Task
from celery.utils.log import get_task_logger
from djcelery.models import TaskMeta
from ..models import Config

LOG = get_task_logger(__name__)

class UpdateTask(Task):

    def __init__(self):
        self.rate_limit = '50/m'
        self.max_retries = 3
        self.default_retry_delay = 60


class OLTPBenchResults(UpdateTask):

    def on_success(self, retval, task_id, args, kwargs):
        super(OLTPBenchResults, self).on_success(retval, task_id, args, kwargs)

        # Completely delete this result because it's huge and not
        # interesting
        #task_meta = TaskMeta.objects.get(task_id=task_id)
        #task_meta.result = None
        #task_meta.save()

@task(base=OLTPBenchResults, name='get_oltpbench_results')
def get_oltpbench_results(result_id):
    # Check that we've completed the background tasks at least once. We need
    # this data in order to make a configuration recommendation (until we
    # implement a sampling technique to generate new training data).
    #latest_pipeline_run = PipelineRun.objects.get_latest()
    print "asynchronous task id {} !!!".format(result_id)
    config = Config.objects.get(pk = result_id)    
    knobs_setting = config.knobs_setting
    print knobs_setting


def newPostgresConfig(knobs_setting, configFile):

    with open(configFile, "r+") as postgresqlconf:
        lines = postgresqlconf.readlines()
        settings_idx = lines.index("# Add settings for extensions here\n")
        postgresqlconf.seek(0)
        postgresqlconf.truncate(0)
        lines = lines[0:(settings_idx + 1)]
        for line in lines:
            postgresqlconf.write(line)

        for (knob_name, knob_value) in list(knobs_setting.items()):
            postgresqlconf.write(str(knob_name) + " = " + str(knob_value) + "\n")





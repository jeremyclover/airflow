import logging
import re

from airflow.hooks import HiveCliHook
from airflow.models import BaseOperator
from airflow.utils import apply_defaults


class HiveOperator(BaseOperator):
    """
    Executes hql code in a specific Hive database.

    :param hql: the hql to be executed
    :type hql: string
    :param hive_cli_conn_id: reference to the Hive database
    :type hive_cli_conn_id: string
    :param hiveconf_jinja_translate: when True, hiveconf-type templating
        ${var} gets translated into jina-type templating {{ var }}. Note that
        you may want to use along this along with the
        ``DAG(user_defined_macros=myargs)`` parameter. View the DAG
        object documentation for more details.
    :type hiveconf_jinja_translate: boolean
    :param script_begin_tag: If defined, the operator will get rid of the
        part of the script before the first occurrence of `script_begin_tag`
    :type script_begin_tag: str
    """

    template_fields = ('hql', 'schema')
    template_ext = ('.hql', '.sql',)
    ui_color = '#f0e4ec'

    @apply_defaults
    def __init__(
            self, hql,
            hive_cli_conn_id='hive_cli_default',
            schema='default',
            hiveconf_jinja_translate=False,
            script_begin_tag=None,
            *args, **kwargs):

        super(HiveOperator, self).__init__(*args, **kwargs)
        self.hiveconf_jinja_translate = hiveconf_jinja_translate
        self.hql = hql
        self.schema = schema
        self.hive_cli_conn_id = hive_cli_conn_id
        self.script_begin_tag = script_begin_tag

    def get_hook(self):
        return HiveCliHook(hive_cli_conn_id=self.hive_cli_conn_id)

    def prepare_template(self):
        if self.hiveconf_jinja_translate:
            self.hql = re.sub(
                "(\$\{([ a-zA-Z0-9_]*)\})", "{{ \g<2> }}", self.hql)
        if self.script_begin_tag and self.script_begin_tag in self.hql:
            self.hql = "\n".join(self.hql.split(self.script_begin_tag)[1:])

    def execute(self, context):
        logging.info('Executing: ' + self.hql)
        self.hook = self.get_hook()
        self.hook.run_cli(hql=self.hql, schema=self.schema)

    def dry_run(self):
        self.hook = self.get_hook()
        self.hook.test_hql(hql=self.hql)

    def on_kill(self):
        self.hook.kill()

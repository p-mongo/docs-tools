#!/usr/bin/python
import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from docs_meta import conf
from utils import get_conf_file, ingest_yaml
from makecloth import MakefileCloth

m = MakefileCloth()

def generate_build_system(data):
    phony = []
    
    if data['check'] is True:
        phony.extend(['_build-check-production', '_build-check-staging'])
        m.target('_build-check-production')
        m.job('fab --parallel --pool-size=2 deploy.production:{0} deploy.check'.format(conf.git.branches.current))
        m.target('_build-check-staging')
        m.job('fab deploy.staging:{0} deploy.check'.format(conf.git.branches.current))
        
    push_cmd = {'push': 'fab --parallel --pool-size=2 --linewise deploy.{0}:{1}',
                'stage': 'fab'}

    for (target, action) in data['env'].items():
        m.section_break('targets for pushing to ' + action)
        phony.extend([target, target_all, target_delete])
        target_all = '-'.join([target, 'all'])
        target_delete = '-'.join([target, 'with', 'delete'])

        if data['check'] is True:
            phony.extend([target + '-if-up-to-date', target + '-if-up-to-date'])
            m.target(target + '-if-up-to-date', ['_build-check-' + action, 'publish'])
            m.target(target, target + '-if-up-to-date')
        else:
            m.target(target, 'publish')
            
        m.msg('[push]: copying the new "{0}" build to the {1} web servers'.format(conf.git.branches.current, action))
        m.job(' '.join([push_cmd[target].format(action, conf.git.branches.current), 'deploy.push', 'deploy.static' ]))
        m.msg('[push]: deployed a new build of the "{0}" branch of the manual to {1}'.format(conf.git.branches.current, action))
    
        m.target(target + '-all', 'publish')
        m.msg('[push]: deploying the full docs site to the {0} web servers'.format(action))
        m.job(' '.join([push_cmd[target].format('production', 'override'), 'deploy.everything:override']))
        m.msg('[push]: deployed a new full build of Manual to the {0} environment'.format(action))
    
        m.target(target + '-with-delete', 'publish')
        m.msg('[push]: copying the new "{0}" build to the {1} web servers (with rsync --delete)'.format(conf.git.branches.current, action))
        m.job(' '.join([push_cmd[target].format('production', conf.git.branches.current), 'deploy.push:delete', 'deploy.static' ]))
        m.msg('[push]: deployed a new build of the "{0}" branch of the manual to the {1} environment'.format(conf.git.branches.current, action))
        m.newline()

    m.target('.PHONY', phony)

def main():
    push_conf = ingest_yaml(get_conf_file(__file__))

    generate_build_system(push_conf)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies  files.')

if __name__ == '__main__':
    main()
 

#/*************************************************************************
# * File Name: start.sh
# * 
# *       Author: aceway
# *         Mail: aceway@qq.com
# * Created Time: 2023年03月04日 星期六 17时21分13秒
# *  Description: ...
# * 
# ************************************************************************
#*/
#

cd `dirname $0`

python --version
django-admin.py --version

ps aux|grep manage.py |grep -w runserver

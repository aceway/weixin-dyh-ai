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

if [ ! -f ./manage.py ];then
    echo "Not found manage.py here"
    pwd
    exit
fi

python --version
djv=`django-admin --version`
echo "Django: ${djv}"

if [ $# -eq 1 ] && [ $1 = "prod" ];then
    python ./manage.py runserver 8888
else
    python ./manage.py runserver 8080
fi

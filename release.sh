#!/usr/bin/env bash
########################################################################
#    File Name: release.sh
# 
#       Author: aceway
#         Mail: aceway@qq.com
# Created Time: Wed 17 Feb 2016 11:12:55 PM CST
#  Description: ...
# 
########################################################################
cd `dirname $0`

. ~/bin/base.sh

cmd='rsync'
rpath='/opt/weixin/dyh/'
user='aceway'
lpath='./'
exclude='./exclude.list'

if [ $# -eq 1 ] && [ $1 = "remote" ] ;then
    rhost='124.222.90.63'
    rport=19806
    rkey='~/.ssh/txyun_rsa'
    dist_from_local_to_remote_with_key ${cmd} ${rhost} ${rport} ${user} ${rkey} ${lpath} ${rpath} ${exclude}
else 
    $cmd -vr --exclude-from ${exclude} --progress ${lpath} ${rpath}
    
fi

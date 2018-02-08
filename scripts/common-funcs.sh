#!/bin/bash

get_parm_from_odoocfg() {
  odoocfgparm=$(cat ../../../etc/odoo.cfg |grep $1 | sed -nr 's/^.*=\s//p' | awk '{$1=$1};1')
}


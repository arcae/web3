#!/usr/bin/env bash



check_subsys_status ()
{
   echo "Hello inside check subsys status method"
   exit 1
}
echo 'Hello from inside main script'
check_subsys_status

echo 'After exit in function call above'
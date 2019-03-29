#|/bin/env bash

cookie=/var/lib/bitcoin/.cookie
if grep -q -- 'OPTIONS=".*--btc-testnet' /etc/sysconfig/otsd
then
        cookie=/var/lib/bitcoin/testnet3/.cookie
fi

until [ -f "$cookie" ]
do
  /bin/sleep 3
done

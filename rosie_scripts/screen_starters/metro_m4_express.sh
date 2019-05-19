#!bin/bash

# Discover board information for: metro_m4_express
find_msc_mount ()
{
    parent_mnt="$(lsblk --pairs -o "MODEL,KNAME" | \
        awk /'Metro M4 Express'/ | \
        awk '
            BEGIN { RS = " " } { FS = "=" }
            /^KNAME/ { print $2 }
        '
    )"
    #echo "parent_mnt: $parent_mnt"

    child_mnt="$(lsblk --pairs -o "PKNAME,MOUNTPOINT" | \
        awk /PKNAME=$parent_mnt/ | \
        awk '
            BEGIN { RS = " "} { FS = "=" }
            /MOUNTPOINT/ { print $2 }
        '
    )"
    #echo "child_mnt: $child_mnt"
    echo "$child_mnt"
}
fs_mnt="$(find_msc_mount)"
echo "mountpoint: "$fs_mnt

get_dev_path ()
{
    for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
        (
            syspath="${sysdevpath%/dev}"
            devname="$(udevadm info -q name -p $syspath)"
            [[ "$devname" != "ttyACM"* ]] && continue
            eval "$(udevadm info -q property --export -p $syspath)"
            [[ -z "$ID_SERIAL" ]] && continue
            [[ "$ID_SERIAL" != *"Metro_M4_Express"* ]] && continue
            echo "$devname"
        )
    done
}
tty_path="$(get_dev_path)"
echo "tty: /dev/"$tty_path

# Start 'screen', naming the session so we can refer to
# it later.
screen -dmSL metro_m4_express -Logfile metro_m4_screen.log '/dev/'$tty_path

# Have screen flush the log output after 1 second (default: 10 seconds)
screen -S metro_m4_express -X logfile flush 1

#!bin/bash

## Discover board information for: metro_m4_express
#  Find the mountpoint for the USB Drive
find_msc_mount ()
{
    local parent_mnt="$(lsblk --pairs -o "MODEL,KNAME" | \
        awk /'Metro M4 Express'/ | \
        awk '
            BEGIN { RS = " " } { FS = "=" }
            /^KNAME/ { print $2 }
        '
    )"
    #echo "parent_mnt: $parent_mnt"

    if [[ "$parent_mnt" != "" ]]; then
        local child_mnt="$(lsblk --pairs -o "PKNAME,MOUNTPOINT" | \
            awk /PKNAME=$parent_mnt/ | \
            awk '
                BEGIN { RS = " "} { FS = "=" }
                /MOUNTPOINT/ { print $2 }
            '
        )"
    fi
    #echo "child_mnt: $child_mnt"

    if [[ "$child_mnt" == "" ]]; then
        echo "NotFound"
    else
        echo "${child_mnt//\"}"
    fi
}
fs_mnt="$(find_msc_mount)"

# Find the device path for use with screen
get_dev_path ()
{
    local tty_tmp="$(\
        for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
        (
            local syspath="${sysdevpath%/dev}"
            local devname="$(udevadm info -q name -p $syspath)"
            [[ "$devname" != "ttyACM"* ]] && continue
            eval "$(udevadm info -q property --export -p $syspath)"
            [[ -z "$ID_SERIAL" ]] && continue
            [[ "$ID_SERIAL" != *"Metro_M4_Express"* ]] && continue
            echo "$devname"
        );
        done
    )"
    if [[ "$tty_tmp" == "" ]]; then
        echo "NotFound"
    else
        echo "/dev/$tty_tmp"
    fi
}
tty_path="$(get_dev_path)"

# Check that we have found all necessary information, and proceed accordingly
if [[ "$tty_path" == "NotFound" ]] || [[ "$fs_mnt" == "NotFound" ]]; then
    # Houston, we have a problem.
    unset ROSIE_METROM4EXPRESS_MNT
    unset ROSIE_METROM4EXPRESS_SCRN

    echo "Error: Metro M4 Express Not Found."
    return 1
else
    echo "Metro M4 Express found:"
    echo " > USB Drive Mountpoint: $fs_mnt"
    echo " > Serial tty: $tty_path"

    # Set environment variables
    export ROSIE_METROM4EXPRESS_MNT="$fs_mnt"
    export ROSIE_METROM4EXPRESS_SCRN="metro_m4_express"

    # Start 'screen', naming the session so we can refer to
    # it later.
    screen -dmSL metro_m4_express -Logfile metro_m4_screen.log $tty_path

    # Have screen flush the log output after 1 second (default: 10 seconds)
    screen -S metro_m4_express -X logfile flush 1
    
fi

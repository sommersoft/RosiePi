#!bin/bash


## Discover board information for: metro_m4_express (METROM4BOOT)
#  Find the mountpoint for the USB Drive
find_msc_mount ()
{
    local parent_mnt="$(lsblk --pairs -o "MODEL,LABEL,MOUNTPOINT,TRAN" | \
        awk /'MODEL=.*Express.*LABEL="METROM4BOOT"'/ | \
        awk '
            BEGIN { RS = " " } { FS = "=" }
            /MOUNTPOINT/ { print $2 }
        '
    )"
    #echo "parent_mnt: $parent_mnt"

    if [[ "$parent_mnt" == "" ]]; then
        echo "NotFound"
    else
        echo "${parent_mnt//\"}"
    fi
}
#find_msc_mount
fs_mnt="$(find_msc_mount)"

# Check that we have found all necessary information, and proceed accordingly
if [[ "$fs_mnt" == "NotFound" ]]; then
    # Houston, we have a problem.
    echo "Metro M4 Express (METROM4BOOT) Not Found."
    exit 1
else
    echo "Metro M4 Express (METROM4BOOT) found:"
    echo " > USB Drive Mountpoint: $fs_mnt"
fi

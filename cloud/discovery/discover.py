from asyncio.subprocess import DEVNULL
import json
import os
import pprint
import subprocess
import paramiko
import sys
import fnmatch

qat_pf_ids = ['0435', '37c8', '19e2', '18ee', '6f54', '18a0', '4940', '4942']
qat_vf_ids = ['0443', '37c9', '19e3', '18ef', '6f55', '18a1', '4941', '4943']
feature_flag_summary = ["sgx", "avx"]

class Remote:
    def __init__(self, ip_addr, username, key_filename):
        self.ip_addr = ip_addr
        self.username = username
        self.key_filename = key_filename
        self.session = None

    def connect(self):
        try:
            self.session = paramiko.SSHClient()
            self.session.load_system_host_keys
            self.session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #if self.pkey is not None:
            #    pkey_file=os.path.expanduser(self.pkey)
            #    print("PKEY: ",pkey_file)
            #else:
            #    pkey_file=os.path.expanduser("~/.ssh/id_rsa")
            #priv_key = paramiko.RSAKey.from_private_key_file(pkey_file)
            #self.session.connect(self.ip_addr, pkey=priv_key)
            self.session.connect(self.ip_addr, username=self.username, key_filename=self.key_filename)
        except paramiko.AuthenticationException as e:
            print("Auth failed: ",e)
            sys.exit()
        except paramiko.SSHException as e:
            print("SSH Connection failed: ",e)
            sys.exit()

    def exec(self, cmd, split=False):
        try:
            _stdin, output, stderr = self.session.exec_command(cmd)
            parse_out = output.read().decode("UTF-8").rstrip('\n')
        except paramiko.SSHException as e:
            print("Command exec failed: ",e)
            return None
        if stderr.read(1):
            return None
        if split:
            return parse_out.splitlines()
        else:
            return parse_out

    def close(self):
        self.close


def check_output(cmd, split=False):
    if remote is not None:
        output = remote.exec(cmd, split=split)
        return output
    try:
        if split:
            output = subprocess.check_output(cmd, shell=True, stderr=DEVNULL).decode("UTF-8").splitlines()
        else:
            output = subprocess.check_output(cmd, shell=True, stderr=DEVNULL).decode("UTF-8")
    except subprocess.CalledProcessError as e:
        return None
    return output

def socket_update(orig: dict, update: dict):
    for i in set(update["Socket"].keys()):
        if i not in orig["Socket"]:
            orig["Socket"].update({i: {}})
        if "Device" in list(set(orig["Socket"][i].keys())&set(update["Socket"][i].keys())):
            orig["Socket"][i]["Device"].update(update["Socket"][i]["Device"])
        else:
            orig["Socket"][i].update(update["Socket"][i])
    return orig


def get_pci_net():
    socket_out = {"Socket": {}}
    global nic_sriov
    global nic_ddp
    global nic_types
    try:
        with open(os.path.join(sys.path[0],"ddp_devs"), 'r') as file:
            for line in file:
                if not line.strip().startswith("#"):
                    ddp_list = line.strip()
                    break
    except IOError as e:
        print("Error loading ddp_devs - Exiting")
        sys.exit()
    net_devices = check_output("ls -1 /sys/class/net/*/device/numa_node", split=True)
    if net_devices is None: return None
    net_numa = check_output("cat /sys/class/net/*/device/numa_node", split=True)
    for (i, h) in zip(net_devices, net_numa):
        h = int(h)
        dev_name = i.split("/")[4]
        device = {dev_name: {}}
        dev_path = os.path.split(i)
        uevent_dump =  check_output("cat %s/uevent" % dev_path[0])
        for line in uevent_dump.splitlines():
            linevals = list(map(str.strip, line.split('=', 1)))
            device[dev_name].update({linevals[0].title(): linevals[1]})
        pci_slot = device[dev_name]["Pci_Slot_Name"].split(':', 1)[1]
        del device[dev_name]["Pci_Slot_Name"]
        device[dev_name].update({"Interface": dev_name})
        pci_subsystem = check_output("lspci -s %s -v | grep Subsystem" % pci_slot)
        if pci_subsystem:
            pci_subsystem = pci_subsystem.split(':')[1].strip()
        else:
            try:
                pci_subsystem = check_output("lspci -s %s" % pci_slot).split(':')[2]
                if pci_subsystem:
                    pci_subsystem = pci_subsystem.strip()
                else:
                    pci_subsystem = "Unknown"
            except AttributeError:
                pci_subsystem = "Unknown"
        device[dev_name].update({"Device": pci_subsystem})
        device[pci_slot] = device[dev_name]
        del device[dev_name]
        if "Pci_Id" in device[pci_slot].keys():
            if device[pci_slot]["Pci_Id"] in ddp_list:
                device[pci_slot].update({"Ddp_Support": True})
                if not nic_ddp:
                    nic_ddp = True
        if "Driver" in device[pci_slot].keys():
            if device[pci_slot]["Driver"] == "ice":
                if "cvl" not in nic_types:
                    nic_types.append("cvl")
            elif device[pci_slot]["Driver"] == "i40e":
                if "fvl" not in nic_types:
                    nic_types.append("fvl")

        ## Get information about PF/VF and SR-IOV
        ## Check for SR-IOV Capabilities
        ########## CONTINUE WORKING ON THIS, MAKE SURE ALL INTERFACES HAVE RELEVANT INFO
        totalvfs = check_output("cat %s/sriov_totalvfs" % dev_path[0])
        if totalvfs is not None and int(totalvfs) > 0:
            # PF with SR-IOV enabled
            device[pci_slot].update({"Sriov_Enabled": True})
            nic_sriov = True
            device[pci_slot].update({"Sriov_Maxvfs": int(totalvfs)})
            device[pci_slot].update({"Type": "PF"})
            vf_list = check_output("cat %s/virtfn*/uevent | grep PCI_SLOT_NAME" % dev_path[0], split=True)
            if vf_list is not None:
                # PF with SR-IOV enabled and VFs configured
                device[pci_slot].update({"Sriov_Vf_Count": len(vf_list)})
                vf_pcis = []
                for vf in vf_list:
                    pci = vf.split('=', 1)[1].strip()
                    vf_pcis.append(pci.split(':', 1)[1])
                device[pci_slot].update({"Vf_Pci_Ids": vf_pcis})
        else:
            pf_id = check_output("cat %s/physfn/uevent | grep PCI_SLOT_NAME" % dev_path[0])
            if pf_id is None:
                # PF without SR-IOV
                device[pci_slot].update({"Type": "Pf"})
                device[pci_slot].update({"Sriov_Enabled": False})
            else:
                # VF
                short_id = pf_id.split('=', 1)[1].strip().split(':', 1)[1]
                device[pci_slot].update({"Pf_Pci_Id": short_id})
                device[pci_slot].update({"Type": "Vf"})
        if h not in socket_out["Socket"]:
            socket_out["Socket"].update({h: {}})
            socket_out["Socket"][h].update({"Device": {"Nic": {}}})
        socket_out["Socket"][h]["Device"]["Nic"].update(device)
    return socket_out

def get_pci_qat():
    pf_ids = []
    vf_ids = []
    socket_out = {"Socket": {}}
    global qat_sriov
    dev_path = "/sys/bus/pci/devices/0000:"
    pci_devices = check_output("lspci -nmm", split=True)
    if not pci_devices:
        return None
    for device in pci_devices:
        for pf_id in qat_pf_ids:
            if pf_id in device:
                pf_ids.append(device.split()[0])
        for vf_id in qat_vf_ids:
            if vf_id in device:
                vf_ids.append(device.split()[0])
    if len(pf_ids) == 0 and len(vf_ids) == 0: return None
    for pf_id in pf_ids:
        device = {pf_id: {}}
        qat_numa = int(check_output("cat %s%s/numa_node" % (dev_path, pf_id)))
        uevent_dump =  check_output("cat %s%s/uevent" % (dev_path, pf_id))
        pci_subsystem = check_output("lspci -s %s -v | grep Subsystem" % pf_id)
        if pci_subsystem:
            pci_subsystem = pci_subsystem.split(':')[1].strip()
        else:
            try:
                pci_subsystem = check_output("lspci -s %s" % pf_id).split(':')[2]
                if pci_subsystem:
                    pci_subsystem = pci_subsystem.strip()
                else:
                    pci_subsystem = "Unknown"
            except AttributeError:
                pci_subsystem = "Unknown"
        for line in uevent_dump.splitlines():
            linevals = list(map(str.strip, line.split('=', 1)))
            device[pf_id].update({linevals[0].title(): linevals[1]})
        del device[pf_id]["Pci_Slot_Name"]
        device[pf_id].update({"Device": pci_subsystem})
        device[pf_id].update({"Type": "PF"})
        totalvfs = check_output("cat %s%s/sriov_totalvfs" % (dev_path, pf_id))
        if totalvfs is not None and int(totalvfs) > 0:
            # PF with SR-IOV enabled
            device[pf_id].update({"Sriov_Enabled": True})
            qat_sriov = True
            device[pf_id].update({"Sriov_Maxvfs": int(totalvfs)})
            vf_list = check_output("cat %s%s/virtfn*/uevent | grep PCI_SLOT_NAME" % (dev_path, pf_id), split=True)
            if vf_list is not None:
                # PF with SR-IOV enabled and VFs configured
                device[pf_id].update({"Sriov_Vf_Count": len(vf_list)})
                vf_pcis = []
                for vf in vf_list:
                    pci = vf.split('=', 1)[1].strip()
                    vf_pcis.append(pci.split(':', 1)[1])
                device[pf_id].update({"Vf_Pci_Ids": vf_pcis})
        if qat_numa not in socket_out["Socket"]:
            socket_out["Socket"].update({qat_numa: {}})
            socket_out["Socket"][qat_numa].update({"Device": {"Qat": {}}})
        socket_out["Socket"][qat_numa]["Device"]["Qat"].update(device)

    for vf_id in vf_ids:
        device = {vf_id: {}}
        qat_numa = int(check_output("cat %s%s/numa_node" % (dev_path, vf_id)))
        uevent_dump =  check_output("cat %s%s/uevent" % (dev_path, vf_id))
        pci_subsystem = check_output("lspci -s %s -v | grep Subsystem" % vf_id)
        if pci_subsystem:
            pci_subsystem = pci_subsystem.split(':')[1].strip()
        else:
            pci_subsystem = check_output("lspci -s %s" % vf_id).split(':')[2]
            if pci_subsystem:
                pci_subsystem = pci_subsystem.strip()
            else:
                pci_subsystem = "Unknown"
        pf_sub_id = check_output("cat %s%s/physfn/uevent | grep PCI_SLOT_NAME" % (dev_path, vf_id))
        for line in uevent_dump.splitlines():
            linevals = list(map(str.strip, line.split('=', 1)))
            device[vf_id].update({linevals[0].title(): linevals[1]})
        del device[vf_id]["Pci_Slot_Name"]
        device[vf_id].update({"Device": pci_subsystem})
        device[vf_id].update({"Type": "Vf"})
        if pf_sub_id is not None:
            # VF
            short_id = pf_sub_id.split('=', 1)[1].strip().split(':', 1)[1]
            device[vf_id].update({"Pf_Pci_Id": short_id})
            device[vf_id].update({"Type": "Vf"})
        if qat_numa not in socket_out["Socket"]:
            socket_out["Socket"].update({qat_numa: {}})
            socket_out["Socket"][qat_numa].update({"Device": {"Qat": {}}})
        socket_out["Socket"][qat_numa]["Device"]["Qat"].update(device)
    return socket_out

def get_lscpu():
    lscpu_out = {}
    cpu_info_json = check_output("lscpu -J")
    if cpu_info_json is None: return None
    json_object = json.loads(cpu_info_json)
    for i in json_object['lscpu']:
        lscpu_out[i['field'].replace(":","")] = i['data']
    return {"lscpu": lscpu_out}

def get_core_info():
    socket_out = {"Socket": {}}
    core_info_csv = check_output("lscpu -p=cpu,core,socket,node,cache")
    if core_info_csv is None: return None
    for i in core_info_csv.splitlines():
        # CPU, Core, Socket, Node, Cache
        if i and not i.startswith("#"):
            cpustats = i.split(",")
            cpu_id = int(cpustats[0])
            core_id = int(cpustats[1])
            socket_id = int(cpustats[2])
            if cpustats[3]:
                node_id = int(cpustats[3])
            else:
                node_id = None
            cache = str(cpustats[4])

            if socket_id not in socket_out["Socket"]:
                socket_out["Socket"].update({socket_id: {"Cores": {}}})
            if core_id not in socket_out["Socket"][socket_id]["Cores"]:
                socket_out["Socket"][socket_id]["Cores"].update({core_id: {"Cpus": []}})
            #print(socket_out["Socket"][socket_id]["Core"][core_id])
            socket_out["Socket"][socket_id]["Cores"][core_id]["Cpus"].append(cpu_id)
            if node_id is not None and "Node" not in socket_out["Socket"][socket_id]["Cores"][core_id].keys():
                socket_out["Socket"][socket_id]["Cores"][core_id].update({"Node": node_id})
            if "Cache" not in socket_out["Socket"][socket_id]["Cores"][core_id].keys():
                socket_out["Socket"][socket_id]["Cores"][core_id].update({"Cache": cache})
    return socket_out

def get_socket_mem_info():
    socket_out = {"Socket": {}}
    mem_nodes = check_output("ls -1 /sys/devices/system/node/node*/meminfo", split=True)
    if mem_nodes is None: return None
    for i in mem_nodes:
        socket = int(i.split("/")[5].lstrip('node'))
        socket_out["Socket"].update({socket: {"Memory": {}}})
        memdump = check_output("cat %s" % i)
        for h in memdump.splitlines():
            valpair = h.split()[2:4]
            socket_out["Socket"][socket]["Memory"].update({valpair[0].lstrip(':'): valpair[1]})
    return socket_out

def get_mem_info():
    # Add to full output
    meminfo_out = {"Memory": {}}
    mem_info = check_output("cat /proc/meminfo", split=True)
    if mem_info is None: return None
    for i in mem_info:
        valpair = i.split()[0:2]
        meminfo_out["Memory"].update({valpair[0].rstrip(':'): valpair[1]})
    return meminfo_out

def get_host_info():
    hostinfo_out = {"Host": {}}
    # consider changing to /etc/os-release if hostnamectl is not common
    host_info = check_output("hostnamectl", split=True)
    if host_info:
        for i in host_info:
            value = i.split(':', 1)[1].strip()
            if "Static hostname" in i:
                hostinfo_out["Host"].update({"Hostname": value})
            elif "Operating System" in i:
                hostinfo_out["Host"].update({"OS": value})
            elif "Kernel" in i:
                hostinfo_out["Host"].update({"Kernel": value})
            elif "Architecture" in i:
                hostinfo_out["Host"].update({"Arch": value})
    codename = check_output("cat /sys/devices/cpu/caps/pmu_name")
    if codename:
        codename = codename.strip()
        hostinfo_out["Host"].update({"Codename": codename.title()})
    if not hostinfo_out["Host"].keys(): return None
    return hostinfo_out

def get_summary(info: dict):
    summary = {}
    # summarize existing object
    if "Memory" in info.keys():
        if "HugePages_Total" in info["Memory"]:
            if int(info["Memory"]["HugePages_Total"]) != 0:
                summary["Hugepages_Total"] = info["Memory"]["HugePages_Total"]
                summary["Hugepages_Free"] = info["Memory"]["HugePages_Free"]
                if info["Memory"]["Hugepagesize"] == "1048576":
                    summary["Hugepage_Size"] = "1G"
                elif info["Memory"]["Hugepagesize"] == "2048":
                    summary["Hugepage_Size"] = "2M"
                else:
                    summary["Hugepage_Size"] = info["Memory"]["Hugepagesize"]+"K"
    if "lscpu" in info.keys():
        if "Model name" in info["lscpu"]:
            summary["Cpu_Model"] = info["lscpu"]["Model name"]
        if "CPU(s)" in info["lscpu"]:
            summary["Cpu_Count"] = info["lscpu"]["CPU(s)"]
        if "Socket(s)" in info["lscpu"]:
            summary["Sockets"] = info["lscpu"]["Socket(s)"]
        if "Core(s) per socket" in info["lscpu"]:
            summary["Cores_Per_Socket"] = info["lscpu"]["Core(s) per socket"]
        if "Thread(s) per core" in info["lscpu"]:
            summary["Threads_Per_Core"] = info["lscpu"]["Thread(s) per core"]
        if "NUMA node(s)" in info["lscpu"]:
            summary["Numa_Nodes"] = info["lscpu"]["NUMA node(s)"]
            if int(summary["Numa_Nodes"]) != 0:
                for i in range(int(summary["Numa_Nodes"])):
                    summary["Numa_Node"+str(i)+"_Cpus"] = info["lscpu"]["NUMA node"+str(i)+" CPU(s)"]
        if "Flags" in info["lscpu"]:
            flags = info["lscpu"]["Flags"].split()
            for i in feature_flag_summary:
                matches = fnmatch.filter(flags,i+"*")
                if matches:
                    summary[i.title()] = matches
            if "Virtualization" in info["lscpu"]:
                if "VT-x" in info["lscpu"]["Virtualization"]:
                    if "vmx" in flags:
                        summary["Virtualization"] = True
    if nic_sriov:
        summary["Nic_Sriov"] = True
    if qat_sriov:
        summary["Qat_Sriov"] = True
    if nic_ddp:
        summary["Nic_Ddp"] = True
    if nic_types:
        summary["Nic_Types"] = nic_types

    if not summary:
        return None
    summary_out = {"Summary": summary}
    return summary_out

def main(ip_addr, username, key_filename):
    global remote
    remote = Remote(ip_addr, username, key_filename)
    remote.connect()
    output = {"Socket": {}}
    global nic_sriov
    nic_sriov = False
    global nic_types
    nic_types = []
    global qat_sriov
    qat_sriov = False
    global nic_ddp
    nic_ddp = False
    pci_net = get_pci_net()
    pci_qat = get_pci_qat()
    core_info = get_core_info()
    if pci_net is not None:
        socket_update(output, pci_net)
    if pci_qat is not None:
        socket_update(output, pci_qat)
    if core_info is not None:
        socket_update(output, core_info)
    output.update(get_lscpu())
    socket_mem_info = get_socket_mem_info()
    mem_info = get_mem_info()
    host_info = get_host_info()
    if mem_info is not None:
        output.update(mem_info)
    if socket_mem_info is not None:
        socket_update(output, socket_mem_info)
    if host_info is not None:
        output.update(host_info)
    summary_info = get_summary(output)
    if summary_info is not None:
        output.update(summary_info)

    print(json.dumps(output))
    if remote is not None:
        remote.close()
    return output


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1], sys.argv[2], sys.argv[3])

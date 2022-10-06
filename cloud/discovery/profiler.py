import discover
import yaml
import pprint
import os
import sys

dists = ["RedHat", "Rocky", "Ubuntu"]
dist_vers = ['8.5', '20.04', '21.10', '22.04']
# Verify pmu_name for SPR below
archs = ["skylake", "cascadelake", "icelake", "sapphirerapids"]

class Features:
    def __init__(self, plat: dict):
        self.plat = plat
        self.dist_support = self._check_distro()
        self.codename = self._get_codename()
        self.nics = self._get_nic_types()
        feature_reqs = self._load_yaml("feature_reqs.yml")
        self.feat_reqs = feature_reqs["features"]
        self.sub_feat_reqs = feature_reqs["sub_features"]
        self.profiles = self._load_yaml("profiles.yml")

    def _load_yaml(self, featfile: str):
        try:
            with open(os.path.join(sys.path[0],featfile), 'r') as file:
                try:
                    output = parsed_yaml=yaml.safe_load(file)
                except yaml.YAMLError as exc:
                    print("Error parsing %s - Exiting" % featfile)
                    sys.exit()
            return output
        except IOError as e:
            print("Error loading %s - Exiting" % featfile)
            sys.exit()

    def _get_codename(self):
        if "Host" not in self.plat.keys():
            print("No host information available")
            return None
        if "Codename" not in self.plat["Host"].keys():
            print("No Codename information available")
            return None
        codename = self.plat["Host"]["Codename"]
        if not codename: return None
        if codename.lower() not in archs: return None
        return codename.lower()

    def _get_nic_types(self):
        if "Summary" not in self.plat.keys():
            print("No summary information available")
            return None
        if "Nic_Types" not in self.plat["Summary"].keys():
            return None
        nics = self.plat["Summary"]["Nic_Types"]
        if not nics: return None
        return nics

    def _check_distro(self):
        match = False
        if "Host" not in self.plat.keys():
            print("No host information available")
            return None
        if "OS" not in self.plat["Host"].keys():
            print("No OS information available")
            return None
        for d in dists:
            if d in self.plat["Host"]["OS"]:
                for dv in dist_vers:
                    if dv in self.plat["Host"]["OS"]:
                        match = True
                        break
            if match: break
        if not match:
            return None
        return match

def check_feat_support(key, feats):
    reqs = feats.feat_reqs
    if key in reqs.keys():
        for lim_type in reqs[key].keys():
            if lim_type == "arch":
                if feats.codename not in reqs[key][lim_type]:
                    return False
            elif lim_type == "nic":
                if not any(i in feats.nics for i in reqs[key][lim_type]):
                    return False
    return True

def check_sub_feat_support(key, byo_sub_dict, feats):
    output_dict = {}
    reqs = feats.sub_feat_reqs
    if key in reqs.keys():
        for subfeat in byo_sub_dict.keys():
            if subfeat in reqs[key].keys():
                for lim_type in reqs[key][subfeat].keys():
                    if lim_type == "arch":
                        if feats.codename not in reqs[key][subfeat][lim_type]:
                            output_dict.update({subfeat: "Unsupported"})
                            break
                    elif lim_type == "nic":
                        if not any(i in feats.nics for i in reqs[key][subfeat][lim_type]):
                            output_dict.update({subfeat: "Unsupported"})
                            break
            else:
                output_dict.update({subfeat: True})
    else:
        for subfeat in byo_sub_dict.keys():
             output_dict.update({subfeat: True})
    return output_dict

def byo_check(plat: dict, feats: object):
    output = {}
    if "build_your_own" not in feats.profiles.keys():
        return None
    byo_list = feats.profiles["build_your_own"].keys()
    byo_dict = feats.profiles["build_your_own"]
    for key in byo_list:
        if type(byo_dict[key]) == dict:
            feat_support = check_feat_support(key, feats)
            if feat_support is False:
                support = "Unsupported"
            else:
                support = check_sub_feat_support(key, byo_dict[key], feats)
            output.update({key: support})
        else:
            feat_support = check_feat_support(key, feats)
            if feat_support is False:
                support = "Unsupported"
            else:
                support = check_feat(key, feats)
            output.update({key: support})
    return output

def set_sub_static(subfeats, state):
    feat_dict = {}
    for feat in subfeats.keys():
        feat_dict.update({feat: state})
    return feat_dict

def check_feat(key, feats):
    features = ["sriov_operator", "sriov_network_dp", "qat", "qat_dp", "ddp"] # sgx features covered in arch_features
    unchecked = ["gpu", "gpu_dp", "name", "on_vms", "vm_mode"] # Consider minio (when not test-mode) and physical storage
    if key in unchecked:
        return None
    elif key not in features:
        return True
    if key == "sriov_operator" or key == "sriov_network_dp":
        if "Summary" in feats.plat.keys():
            if "Nic_Sriov" in feats.plat["Summary"]:
                if feats.plat["Summary"]["Nic_Sriov"]:
                    return True
        return False
    if key == "qat" or key == "qat_dp":
        if "Summary" in feats.plat.keys():
            if "Qat_Sriov" in feats.plat["Summary"]:
                if feats.plat["Summary"]["Qat_Sriov"]:
                    return True
        return False
    if key == "ddp":
        if "Summary" in feats.plat.keys():
            if "Nic_Ddp" in feats.plat["Summary"]:
                if feats.plat["Summary"]["Nic_Ddp"]:
                    return True
        return False

def check_profiles(profiles: object, byo_feats: dict):
    summary = {}
    for prof in profiles.keys():
        if prof == "build_your_own":
            continue
        prof_support = True
        summary.update({prof: {"Features": {}}})
        for feat in profiles[prof].keys():
            try:
                if profiles[prof][feat] is True:
                    if byo_feats[feat] is True:
                        summary[prof]["Features"].update({feat: True})
                    elif byo_feats[feat] is False:
                        summary[prof]["Features"].update({feat: False})
                        prof_support = False
                    elif byo_feats[feat] == "Unsupported":
                        summary[prof]["Features"].update({feat: "Unsupported (CPU/NIC)"})
                    elif byo_feats[feat] is None:
                        summary[prof]["Features"].update({feat: "Unchecked (TODO)"})
                elif type(profiles[prof][feat]) is dict:
                    subfeat_set = {}
                    if byo_feats[feat] == "Unsupported":
                        summary[prof]["Features"].update({feat: "Unsupported"})
                        continue
                    elif byo_feats[feat] is None:
                        summary[prof]["Features"].update({feat: "Unchecked (TODO)"})
                        continue
                    for subfeat in profiles[prof][feat].keys():
                        if byo_feats[feat][subfeat] is True:
                            subfeat_set.update({subfeat: True})
                        elif byo_feats[feat][subfeat] is False:
                            subfeat_set.update({subfeat: False})
                            prof_support = False
                        elif byo_feats[feat][subfeat] == "Unsupported":
                            continue
                        elif byo_feats[feat][subfeat] is None:
                            subfeat_set.update({subfeat: "Unchecked (TODO)"})
                    if subfeat_set:
                        summary[prof]["Features"].update({feat: subfeat_set})
            except KeyError:
                print("KeyError (expected): ",feat)
                summary[prof]["Features"].update({feat: "Special feature (not in BYO)"})
        summary[prof].update({"Supported": prof_support})
    if not summary:
        return None
    return summary

def main():
    platform_info = discover.main()
    feats = Features(platform_info)
    if not feats.dist_support:
        print("Unsupported OS distribution and/or version - exiting")
        sys.exit()
    if not feats.codename:
        print("Unsupported CPU codename - exiting")
        sys.exit()
    byo_feats = byo_check(platform_info, feats)
    pprint.pprint(byo_feats)
    full_summary = check_profiles(feats.profiles, byo_feats)
    pprint.pprint(full_summary)
    print("Printing support summary:")
    for profile in full_summary.keys():
        print("  Profile: %s, Supported: %s" % (profile, full_summary[profile]["Supported"]))

if __name__ == "__main__":
    main()
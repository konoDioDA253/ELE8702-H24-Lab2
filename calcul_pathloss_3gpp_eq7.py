### Calcul du pathloss avecv les formules 3GPP
# On considere seulement les scenario RMa, UMa et UMi
import math

# Fonction donnant le group et les coords a partir du ID d'un objet dans une liste du meme objet
def get_group_and_coords_by_id_3GPP(object_list, target_id):
    for object in object_list:
        if object.id == target_id:
            return object.group, object.coords
    return None  

# Fonction calculant la distance entre deux point sur le terrain
def calculate_distance_3GPP(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Fonction permettant de trouver la valeur d'une cle dans un fichier YAML
def get_from_dict_3GPP(key, data, res=None, curr_level = 1, min_level = 1):
    """Fonction qui retourne la valeur de n'importe quel clé du dictionnaire
       key: clé associé à la valeur recherchée
       data: dictionnaire dans lequel il faut chercher
       les autres sont des paramètres par défaut qu'il ne faut pas toucher"""
    if res:
        return res
    if type(data) is not dict:
        msg = f"get_from_dict_3GPP() works with dicts and is receiving a {type(data)}"
        ERROR(msg, 1)
    else:
        # data IS a dictionary
        for k, v in data.items():
            if k == key and curr_level >= min_level:
                #print(f"return data[k] = {data[k]} k = {k}")
                return data[k]
            if type(v) is dict:
                level = curr_level + 1
                res = get_from_dict_3GPP(key, v, res, level, min_level)
    return res 


# # -------------------------------------------------
# #     RMa LOS ET nlOS
# # -------------------------------------------------

# def _rma_nlosp(d_2D, d_Bp, h_Bs, H_UT, W, h):
#     if  d_2D>= && d_2D <= dB
#     PL_RMa = PL1
    
#     return 

# def rma_los():

#     return 


# -------------------------------------------------
#     UMa LOS ET nLOS
# -------------------------------------------------

def uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # Definition des fonctions
    def _uma_los_pl1(distance_3D_m, frequence_GHz):
        pl = 28.0 + 22*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz)
        return pl

    def _uma_los_pl2(distance_3D_m, frequence_GHz, distance_BP_m, hauteur_BS_m, hauteur_UT_m):
        pl = 28.0 + 40*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) - 9*math.log10(distance_BP_m**2 - (hauteur_BS_m - hauteur_UT_m)**2) 
        return pl
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_km = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_m = 1000*distance_2D_km
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))

    distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000

    # Calcul de pathloss
    warning_message = ""
    if 10 < distance_2D_m and distance_2D_m < distance_BP_m :
        pathloss = _uma_los_pl1(distance_3D_m, frequence_GHz)
    if distance_BP_km < distance_2D_km and distance_2D_km < 5 :
        pathloss = _uma_los_pl2(distance_3D_m, frequence_GHz, distance_BP_m, hauteur_BS_m, hauteur_UT_m)
    if distance_2D_m < 10 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = 1000000000000000000000000000000000000000000
    return pathloss, warning_message

def uma_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions
    def max_comparator(pl_los, pl_nlosp, warning_message_uma_los, warning_message_uma_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_uma_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_uma_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_km = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_m = 1000*distance_2D_km
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))

    distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000
    
    
    
    # Calcul de pathloss
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_uma_los = ""
        warning_message_uma_nlosp = ""
        pl_uma_los, warning_message_uma_los = uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_uma_nlosp = 13.54 + 39.08*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) -0.6*(hauteur_UT_m - 1.5)
        pathloss, warning_message = max_comparator(pl_uma_los, pl_uma_nlosp, warning_message_uma_los, warning_message_uma_nlosp)
    if distance_2D_m < 10  :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = 1000000000000000000000000000000000000000000
    return pathloss, warning_message








# # -------------------------------------------------
# #     UMI  LOS ET nLOS
# # -------------------------------------------------

# def umi_los():
#     d_2D, d_Bp, h_UT, H_BS,
#     def _uma_los_pl1(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
#         d2D = calculate_distance(coord1, coord2)
#         d3D_out =  
#         d3D_in = 
#         D3D = sqrt()
#         if d2
#         P_Luma_Los  = PL_1

#         return 

#     def _uma_los_pl2(arg1, arg2, etc):
#         return pl
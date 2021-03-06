#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import datetime
from Utils import UTILS_Titulaires
from Utils import UTILS_Utilisateurs

from Utils import UTILS_Interface
from ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"�")

DICT_TITULAIRES = {}


def DateEngFr(textDate):
    if textDate == None or textDate == "None" : return ""
    text = str(textDate[8:10]) + u"/" + str(textDate[5:7]) + u"/" + str(textDate[:4])
    return text

def DateEngEnDateDD(dateEng):
    if dateEng == None : return None
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))



class Track(object):
    def __init__(self, IDfamille, autorisation_cafpro, dictQuotient=None):
        self.IDfamille = IDfamille
        self.autorisation_cafpro = autorisation_cafpro
        if self.autorisation_cafpro == 1 :
            self.autorisation_cafpro_str = _(u"Oui")
        else :
            self.autorisation_cafpro_str = ""
        self.nomTitulaires = DICT_TITULAIRES[IDfamille]["titulairesSansCivilite"]

        if dictQuotient != None :
            self.date_debut = dictQuotient["date_debut"]
            self.date_fin = dictQuotient["date_fin"]
            self.quotient = dictQuotient["quotient"]
            self.revenu = dictQuotient["revenu"]
            self.observations = dictQuotient["observations"]
        else :
            self.date_debut = None
            self.date_fin = None
            self.quotient = None
            self.revenu = None
            self.observations = None
            


    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.dateReference = None
        self.listeActivites = None
        self.presents = None
        self.familles = "TOUTES"
        self.labelParametres = ""
        self.IDtype_quotient = None

        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
                                
    def InitModel(self):
        global DICT_TITULAIRES
        DICT_TITULAIRES = UTILS_Titulaires.GetTitulaires() 
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        if self.dateReference == None : return []
        if self.IDtype_quotient == None : return []
        
        # Conditions Activites
        if self.listeActivites == None or self.listeActivites == [] :
            conditionActivites = ""
        else:
            if len(self.listeActivites) == 1 :
                conditionActivites = " AND inscriptions.IDactivite=%d" % self.listeActivites[0]
            else:
                conditionActivites = " AND inscriptions.IDactivite IN %s" % str(tuple(self.listeActivites))
                
        # Conditions Pr�sents
##        if self.presents == None :
##            conditionPresents = ""
##            jointurePresents = ""
##        else:
##            conditionPresents = " AND (consommations.date>='%s' AND consommations.date<='%s')" % (str(self.presents[0]), str(self.presents[1]))
##            jointurePresents = "LEFT JOIN consommations ON consommations.IDindividu = individus.IDindividu"

        DB = GestionDB.DB()

        # R�cup�ration des pr�sents
        listePresents = []
        if self.presents != None :
            req = """SELECT IDfamille, inscriptions.IDinscription
            FROM consommations
            LEFT JOIN inscriptions ON inscriptions.IDinscription = consommations.IDinscription
            WHERE date>='%s' AND date<='%s' %s
            GROUP BY IDfamille
            ;"""  % (str(self.presents[0]), str(self.presents[1]), conditionActivites.replace("inscriptions", "consommations"))
            DB.ExecuterReq(req)
            listeIndividusPresents = DB.ResultatReq()
            for IDfamille, IDinscription in listeIndividusPresents :
                listePresents.append(IDfamille)

        # R�cup�ration des familles
##        req = """SELECT familles.IDfamille
##        FROM familles 
##        LEFT JOIN rattachements ON rattachements.IDfamille = familles.IDfamille
##        %s
##        WHERE familles.IDfamille>0 %s %s
##        GROUP BY familles.IDfamille
##        ;""" % (jointurePresents, conditionActivites, conditionPresents)

        req = """
        SELECT inscriptions.IDfamille, familles.autorisation_cafpro
        FROM inscriptions 
        LEFT JOIN individus ON individus.IDindividu = inscriptions.IDindividu
        LEFT JOIN familles ON familles.IDfamille = inscriptions.IDfamille
        AND inscriptions.IDfamille = familles.IDfamille
        LEFT JOIN caisses ON caisses.IDcaisse = familles.IDcaisse
        LEFT JOIN regimes ON regimes.IDregime = caisses.IDregime
        WHERE (inscriptions.date_desinscription IS NULL OR inscriptions.date_desinscription>='%s') %s
        GROUP BY familles.IDfamille
        ;""" % (datetime.date.today(), conditionActivites)

        DB.ExecuterReq(req)
        listeFamilles = DB.ResultatReq()
        
        # R�cup�ration des quotients valides � la date de r�f�rence
        req = """SELECT IDquotient, IDfamille, date_debut, date_fin, quotient, observations, revenu, IDtype_quotient
        FROM quotients
        WHERE date_debut<='%s' AND date_fin>='%s' AND IDtype_quotient=%d
        ORDER BY date_fin
        ;""" % (self.dateReference, self.dateReference, self.IDtype_quotient)
        DB.ExecuterReq(req)
        listeQuotients = DB.ResultatReq()
        dictQuotients = {}
        for IDquotient, IDfamille, date_debut, date_fin, quotient, observations, revenu, IDtype_quotient in listeQuotients :
            dictQuotients[IDfamille] = {"IDquotient":IDquotient, "date_debut":DateEngEnDateDD(date_debut), "date_fin":DateEngEnDateDD(date_fin), "quotient":quotient, "revenu" : revenu, "IDtype_quotient" : IDtype_quotient, "observations":observations}
        
        DB.Close()

        listeListeView = []
        for IDfamille, autorisation_cafpro in listeFamilles :
            
            if self.presents == None or (self.presents != None and IDfamille in listePresents) :
                
                if dictQuotients.has_key(IDfamille) :
                    dictQuotient = dictQuotients[IDfamille]
                else :
                    dictQuotient = None
                    
                if self.familles == "TOUTES" :
                    listeListeView.append(Track(IDfamille, autorisation_cafpro, dictQuotient))
                if self.familles == "AVEC" and dictQuotient != None:
                    listeListeView.append(Track(IDfamille, autorisation_cafpro, dictQuotient))
                if self.familles == "SANS" and dictQuotient == None:
                    listeListeView.append(Track(IDfamille, autorisation_cafpro, dictQuotient))

        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(dateDD):
            return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" or montant == 0.0 : return ""
            return u"%.2f %s" % (montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(_(u"ID"), "left", 0, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_(u"Famille"), 'left', 280, "nomTitulaires", typeDonnee="texte"),
            ColumnDefn(_(u"Acc�s CAFPRO"), "center", 100, "autorisation_cafpro_str", typeDonnee="texte"),
            ColumnDefn(_(u"QF"), "center", 80, "quotient", typeDonnee="entier"),
            ColumnDefn(_(u"Revenu"), 'center', 80, "revenu", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(u"Du", "left", 80, "date_debut", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_(u"Au"), "left", 80, "date_fin", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_(u"Observations"), "left", 250, "observations", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_(u"Aucune famille"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, date_reference=None, listeActivites=None, presents=None, familles="TOUTES", labelParametres="", IDtype_quotient=None):
        self.dateReference = date_reference
        self.listeActivites = listeActivites
        self.presents = presents
        self.familles = familles
        self.labelParametres = labelParametres
        self.IDtype_quotient = IDtype_quotient

        attente = wx.BusyInfo(_(u"Recherche des donn�es..."), self)
        self.InitModel()
        self.InitObjectListView()
        del attente
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """        
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        # Item Ouverture fiche famille
        item = wx.MenuItem(menuPop, 10, _(u"Ouvrir la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)
        
        menuPop.AppendSeparator()
        
        # G�n�ration automatique des fonctions standards
        self.GenerationContextMenu(menuPop, dictParametres=self.GetParametresImpression())

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def GetParametresImpression(self):
        dictParametres = {
            "titre" : _(u"Liste des quotients familiaux/revenus"),
            "intro" : self.labelParametres,
            "total" : _(u"> %s familles") % len(self.donnees),
            "orientation" : wx.PORTRAIT,
            }
        return dictParametres

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez s�lectionn� aucune fiche famille � ouvrir !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(self.dateReference, self.listeActivites, self.presents, self.familles)
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_(u"Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        import time
        t = time.time()
        self.myOlv.MAJ(date_reference=datetime.date(2015, 8, 13), listeActivites=[1, 2, 3, 4], presents=(datetime.date(2015, 1, 1), datetime.date(2015, 12, 31)), familles="TOUTES")
        #print len(self.myOlv.donnees)
        #print "Temps d'execution =", time.time() - t
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

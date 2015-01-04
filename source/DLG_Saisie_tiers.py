#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import GestionDB


class Dialog(wx.Dialog):
    def __init__(self, parent, IDtiers=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent   
        self.IDtiers = IDtiers

        self.label_nom = wx.StaticText(self, wx.ID_ANY, u"Nom :")
        self.ctrl_nom = wx.TextCtrl(self, wx.ID_ANY, u"")
        self.ctrl_nom.SetMinSize((300, -1))

        self.label_observations = wx.StaticText(self, wx.ID_ANY, u"Observations :")
        self.ctrl_observations = wx.TextCtrl(self, wx.ID_ANY, u"", style=wx.TE_MULTILINE)

        self.bouton_aide = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(u"Images/BoutonsImages/Aide_L72.png", wx.BITMAP_TYPE_ANY))
        self.bouton_ok = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(u"Images/BoutonsImages/Ok_L72.png", wx.BITMAP_TYPE_ANY))
        self.bouton_annuler = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(u"Images/BoutonsImages/Annuler_L72.png", wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        # Init contr�les
        if self.IDtiers != None :
            self.SetTitle(u"Modification d'un tiers")
            self.Importation() 
        else :
            self.SetTitle(u"Saisie d'un tiers")

    def __set_properties(self):
        self.ctrl_nom.SetToolTipString(u"Saisissez le nom du tiers")
        self.ctrl_observations.SetToolTipString(u"Saisissez des observations sur le tiers")
        self.bouton_aide.SetToolTipString(u"Cliquez ici pour obtenir de l'aide")
        self.bouton_ok.SetToolTipString(u"Cliquez ici pour valider")
        self.bouton_annuler.SetToolTipString(u"Cliquez ici pour annuler")

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(2, 1, 10, 10)
        
        grid_sizer_haut = wx.FlexGridSizer(3, 2, 10, 10)

        grid_sizer_haut.Add(self.label_nom, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut.Add(self.ctrl_nom, 0, wx.EXPAND, 0)

        grid_sizer_haut.Add(self.label_observations, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut.Add(self.ctrl_observations, 0, wx.EXPAND, 0)

        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.ALL | wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event):
        import UTILS_Aide
        UTILS_Aide.Aide(u"")

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event): 
        if self.Sauvegarde()  == False :
            return
        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)

    def Sauvegarde(self):
        """ Sauvegarde des donn�es """
        nom = self.ctrl_nom.GetValue() 
        observations = self.ctrl_observations.GetValue() 
        
        # Validation des donn�es saisies
        if nom == "" :
            dlg = wx.MessageDialog(self, u"Vous devez obligatoirement saisir un nom !", u"Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return False

        # Sauvegarde
        DB = GestionDB.DB()
        listeDonnees = [ 
            ("nom", nom ),
            ("observations", observations ),
            ]
        if self.IDtiers == None :
            self.IDtiers = DB.ReqInsert("compta_tiers", listeDonnees)
        else :
            DB.ReqMAJ("compta_tiers", listeDonnees, "IDtiers", self.IDtiers)
        DB.Close()

    def Importation(self):
        """ Importation des valeurs """
        DB = GestionDB.DB()
        req = """SELECT nom, observations
        FROM compta_tiers WHERE IDtiers=%d;""" % self.IDtiers
        DB.ExecuterReq(req)
        listeTemp = DB.ResultatReq()
        DB.Close()
        if len(listeTemp) == 0 : return
        nom, observations = listeTemp[0]
        if nom == None : nom = ""
        if observations == None : observations = ""
        
        self.ctrl_nom.SetValue(nom)
        self.ctrl_observations.SetValue(observations)
        
    def GetIDtiers(self):
        return self.IDtiers



if __name__ == u"__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
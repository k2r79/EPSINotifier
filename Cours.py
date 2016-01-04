#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Cours:
    def __init__(self, matiere, prof, horaires, salle):
        self.matiere = matiere
        self.prof = prof
        self.horaire_debut = horaires[0]
        self.horaire_fin = horaires[1]
        self.salle = salle

    def __str__(self):
        return "%s - %s - [%s - %s] - %s" % (self.matiere, self.prof, self.horaire_debut, self.horaire_fin, self.salle)
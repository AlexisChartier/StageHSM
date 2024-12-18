library(dplyr)
library(shiny)
library(leaflet)
library(shinyscreenshot)
library(gstat)
library(sp)
library(raster)
library(FRK)
library(rgdal)
library(png)
library(tidyr)
library(shinyWidgets)

# Vérifier que le répertoire 'www' existe
if(!dir.exists("www")){
  dir.create("www")
}

addResourcePath(prefix = "www", directoryPath = "./www")

PAGE_TITLE <- "VerdansonPluie"

ui <- fluidPage(
  tags$head(tags$script(src = "www/message-handler.js")),
  screenshotButton(timer = 2, scale = 2, selector = "body"),
  tags$style(type="text/css",
             "h1 {
               text-align:center;
             }",
             "h3 {
               font-family: 'Arial black';
               color: #3399CC ;
               margin-top: 0.2em;
               text-align:center;
             }",
             "h6 {
               color: #ff0000 ;
               margin-top: 0.2em;
               text-align:center;
             }",
             ".box-body {height:80vh}"
  ),

  titlePanel(windowTitle = PAGE_TITLE,
             title=div(h1(img(src="www/images.png", height = 60, width = 330, style = "margin:auto")),h3("Verdanson Pluie"),h6(textOutput("currentTime")))),

  # Sélecteur pour choisir l'un des 7 derniers jours
  selectInput("selected_date", "Sélectionnez une date :", choices = NULL),

  selectInput("cumul", NULL, 
               c("Pluie tombée sur les dernières 15 minutes" = "P15min",
                 "Pluie tombée sur les dernières 30 minutes" = "P30min",
                 "Pluie tombée sur la dernière 1h" = "P1h",
                 "Pluie tombée sur les dernières 2h" = "P2h",
                 "Pluie tombée sur les dernières 4h" = "P4h",
                 "Pluie tombée sur les dernières 12h" = "P12h",
                 "Pluie tombée sur les dernières 24h" = "P24h",
                 "Pluie tombée sur les dernières 48h" = "P48h",
                 "Pluie tombée sur les dernières 72h" = "P72h"
                ),
              width = 350),

  mainPanel(
    h5(textOutput("selected_timestamp")),
    leafletOutput("mymap"), width=14
  )
)

server <- function(input, output, session) {

  # Suppression des fichiers de cumul antérieurs à 7 jours
  data_dir <- "."  # Remplacez par le chemin réel si nécessaire
  files <- list.files(path = data_dir, pattern = "^Pluvio_mtp_AAA_\\d{8}\\.csv$", full.names = TRUE)
  current_date <- Sys.Date()

  for (file in files) {
    filename <- basename(file)
    date_str <- sub("^Pluvio_mtp_AAA_(\\d{8})\\.csv$", "\\1", filename)
    file_date <- as.Date(date_str, format = "%Y%m%d")

    # Calcul de l'âge du fichier en jours
    age <- as.numeric(difftime(current_date, file_date, units = "days"))

    # Suppression du fichier s'il a plus de 7 jours
    if (!is.na(age) && age > 7) {
      file.remove(file)
      cat("Fichier supprimé :", file, "\n")
    }
  }
  # Timer pour actualiser toutes les 2 minutes
  autoInvalidate <- reactiveTimer(120000)

  # Mise à jour de l'heure actuelle
  output$currentTime <- renderText({
    invalidateLater(1000)
    paste("Temps TU :", format(Sys.time(), " %X %a %b %d %Y"))
  })

  # Générer les choix pour le sélecteur de dates
  observe({
    dates <- seq(Sys.Date() - 6, Sys.Date(), by = "days")
    dates_formatted <- format(dates, "%Y-%m-%d")
    updateSelectInput(session, "selected_date", choices = dates_formatted, selected = tail(dates_formatted, n = 1))
  })

  output$mymap <- renderLeaflet({
    # Actualisation toutes les 2 minutes
    autoInvalidate()
    labattrib = paste("<FONT COLOR = black>", "<STRONG>", "OMSEV Hydrosciences; Projet EVIdENCE", "</STRONG>", "</FONT>")

    # Récupérer la date sélectionnée
    selected_date <- input$selected_date
    if (is.null(selected_date)) {
      return(NULL)
    }
    date_str <- gsub("-", "", selected_date)  # Format YYYYMMDD

    # Chemin du fichier correspondant
    data_file <- paste0("Pluvio_Mtp_AAA_", date_str, ".csv")

    # Vérifier si le fichier existe
    if (!file.exists(data_file)) {
      showNotification(paste("Les données pour la date", selected_date, "ne sont pas disponibles."), type = "error")
      return(NULL)
    }

    # Lecture des données de cumul
    DataP <- read.csv(data_file, header = TRUE, stringsAsFactors = FALSE)
    # Conversion de 'latest_time' en POSIXct
    DataP$latest_time <- as.POSIXct(DataP$latest_time, format="%Y-%m-%dT%H:%M:%OS", tz="UTC")

    # Données de cumul sélectionnées
    data <- switch(input$cumul,
                   "P15min" = DataP$P15min,
                   "P30min" = DataP$P30min,
                   "P1h" = DataP$P1h,
                   "P2h" = DataP$P2h,
                   "P4h" = DataP$P4h,
                   "P12h" = DataP$P12h,
                   "P24h" = DataP$P24h,
                   "P48h" = DataP$P48h,
                   "P72h" = DataP$P72h)

    # Calcul du nombre de stations avec données non nulles
    non_nul = sum(!is.na(data) & data > 0)
    datana <- data[!is.na(data) & data > 0]

    # Coordonnées du centre de la carte
    x_centre = 3.85667372
    y_centre = 43.62999968

    # Mise à jour du timestamp sélectionné
    latest_time <- max(DataP$latest_time, na.rm = TRUE)
    output$selected_timestamp <- renderText({
      paste("Dernier cumul disponible le :", format(latest_time, "%Y-%m-%d %H:%M:%S"))
    })

    # Création des labels pour les popups, incluant la dernière heure de donnée
    lab = paste0(DataP$site, " : ", data, " mm",
                 "<br />", "Dernière donnée reçue le ", format(DataP$latest_time, "%Y-%m-%d %H:%M:%S"))

    # Création de la palette de couleurs
    couleurs <- colorNumeric("Blues", range(data, na.rm = TRUE), reverse=FALSE)

    # Si plusieurs stations ont des données
    if (non_nul > 1) {
      # Préparation des données pour l'interpolation
      pts <- data.frame(cumul = data, lon = DataP$lon, lat = DataP$lat)
      raindegre <- na.omit(pts)
      coordinates(raindegre) <- ~lon+lat

      # Définition du CRS
      crs_obj <- CRS("+init=epsg:4326")

      # Définir la grille pour l'interpolation
      lon_lim <- c(3.733,3.933)
      lat_lim <- c(43.588,43.690)
      x.range <- as.numeric(lon_lim)
      y.range <- as.numeric(lat_lim)
      grd <- expand.grid(x = seq(x.range[1], x.range[2], by = 0.00125),
                         y = seq(y.range[1], y.range[2], by = 0.00100))
      coordinates(grd) <- ~x + y
      gridded(grd) <- TRUE
      fullgrid(grd) <- TRUE

      # Interpolation IDW
      idw.res <- idw(formula = cumul ~ 1, locations = raindegre, newdata = grd)
      r = raster(idw.res)
      proj4string(r) <- crs_obj

      # Masque
      Data_Masque <- read.table("Masq_pluvio_teletransmis2.csv", sep=';', dec=".", header=TRUE)
      SpMasque <- df_to_SpatialPolygons(Data_Masque,"id",c("lon","lat"), crs_obj)
      proj4string(SpMasque) <- crs_obj
      r_masque = mask(r, SpMasque)

      # Palette de couleurs pour le raster
      couleurs_raster <- colorNumeric("Blues", values(r), reverse=FALSE, na.color = "transparent")

      # Création de la carte
      leaflet() %>%
        addProviderTiles("OpenStreetMap.DE",
                         options = providerTileOptions(noWrap = TRUE), group = 'OSM') %>%
        setView(lng = x_centre, lat = y_centre, zoom =14 ) %>%
        addMeasure(position = "bottomleft",
                   primaryLengthUnit = "meters",
                   primaryAreaUnit = "sqmeters",
                   activeColor = "#3D535D",
                   completedColor = "#7D4479") %>%
        addTiles(attribution = lapply(labattrib, HTML), group = 'rasterPluie') %>%
        addRasterImage(r_masque, colors = couleurs_raster, opacity = 0.8, group = 'rasterPluie')  %>%
        addProviderTiles(providers$CartoDB.PositronOnlyLabels, group = 'rasterPluie') %>%
        addMarkers(DataP$lon, DataP$lat, icon = makeIcon("www/pluviometre.png", 12, 12),
                   popup = lab, group = 'rasterPluie') %>%
        addTiles(attribution = lapply(labattrib, HTML)) %>%
        addCircleMarkers(DataP$lon, DataP$lat, weight = 2,
                         radius = sqrt(data) * 4,
                         popup = lapply(lab, HTML),
                         color="black", stroke=TRUE,
                         fillColor = couleurs(data),
                         fillOpacity = 0.7, group = "bulles_pluie") %>%
        addLegend(pal = couleurs, values = datana, title = "Pluie mm", opacity = 0.9, group = "bulles_pluie") %>%
        addLayersControl(
          baseGroups = c("OSM"),
          overlayGroups =  c( "bulles_pluie","rasterPluie"),
          options = layersControlOptions(collapsed = FALSE)
        )
    } else if (non_nul == 1) {
      # Une seule station a des données
      leaflet() %>%
        addProviderTiles("OpenStreetMap.DE",
                         options = providerTileOptions(noWrap = TRUE), group = 'OSM') %>%
        setView(lng = x_centre, lat = y_centre, zoom =14)%>%
        addMeasure(position = "bottomleft",
                   primaryLengthUnit = "meters",
                   primaryAreaUnit = "sqmeters",
                   activeColor = "#3D535D",
                   completedColor = "#7D4479")%>%
        addTiles(attribution = lapply(labattrib, HTML), group = 'rasterPluie') %>%
        addCircleMarkers(DataP$lon, DataP$lat, weight = 2,
                         radius = sqrt(data) * 4,
                         popup = lab,
                         color="black", stroke=TRUE,
                         fillColor = "blue",
                         fillOpacity = 0.7, group = 'rasterPluie') %>%
        addTiles(attribution = lapply(labattrib, HTML)) %>%
        addMarkers(DataP$lon, DataP$lat, icon = makeIcon("www/pluviometre.png", 12, 12),
                   popup = lab)%>%
        addCircleMarkers(DataP$lon, DataP$lat, weight = 2,
                         radius = sqrt(data) * 4,
                         popup = lab,
                         color="black", stroke=TRUE,
                         fillColor = "blue",
                         fillOpacity = 0.7, group = "bulles_pluie")  %>%
        addLayersControl(
          baseGroups = c("OSM"),
          overlayGroups = c( "bulles_pluie","rasterPluie"),
          options = layersControlOptions(collapsed = FALSE)
        )
    } else {
      # Aucune station n'a de données
      lab_no_rain = paste("Pas de pluie au niveau des pluviographes ",
                          "</p>", "<center>", "sur la période sélectionnée", "</center>")
      leaflet() %>%
        addProviderTiles("OpenStreetMap.DE",
                         options = providerTileOptions(noWrap = TRUE)) %>%
        setView(lng = x_centre, lat = y_centre, zoom = 11) %>%
        addMeasure(position = "bottomleft",
                    primaryLengthUnit = "meters",
                    primaryAreaUnit = "sqmeters",
                    activeColor = "#3D535D",
                    completedColor = "#7D4479")%>%
        addTiles(attribution = lapply(labattrib, HTML)) %>%
        addMarkers(DataP$lon, DataP$lat, icon =  makeIcon("www/pluviometre.png", 12, 12),
                   popup = paste(DataP$site, " : ", "0.0", "mm"))%>%
        addLabelOnlyMarkers(lng=3.85, lat=43.61,
                            label = lapply(lab_no_rain, HTML),
                            labelOptions = labelOptions(noHide = T, direction = "bottom",
                                                        style = list(
                                                          "color" = "red",
                                                          "font-family" = "serif",
                                                          "font-style" = "italic",
                                                          "font-size" = "14px",
                                                          "border-color" = "rgba(0,0,0,0.5)"
                                                        )))
    }
  })
}

shinyApp(ui, server)

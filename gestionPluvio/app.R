# Chargement des packages nécessaires
library(shiny)
library(leaflet)
library(dplyr)
library(raster)
library(sp)
library(gstat)
library(shinyscreenshot)
library(rgdal)
library(png)
library(tidyr)
library(shinyWidgets)
library(lubridate)
library(ggplot2)

# Vérifier que le répertoire 'www' existe
if(!dir.exists("www")){
  dir.create("www")
}

addResourcePath(prefix = "www", directoryPath = "./www")

PAGE_TITLE <- "Analyse des Cumuls de Pluie"

ui <- fluidPage(
  tags$head(tags$script(src = "www/message-handler.js")),
  screenshotButton(timer = 2, scale = 2, selector = "body"),

  tags$style(type="text/css", HTML("
    h1 {
      text-align:center;
    }
    h3 {
      font-family: 'Arial black';
      color: #3399CC;
      margin-top: 0.2em;
      text-align:center;
    }
    h6 {
      color: #ff0000;
      margin-top: 0.2em;
      text-align:center;
    }
    .box-body {height:80vh;}
  ")),

  titlePanel(
    title = div(
      h1(img(src="www/images.png", height = 60, width = 330, style = "margin:auto")),
      h3("Analyse des Cumuls de Pluie"),
      h6(textOutput("currentTime"))
    ),
    windowTitle = PAGE_TITLE
  ),

  sidebarLayout(
    sidebarPanel(
      airDatepickerInput(
        inputId = "start_datetime",
        label = "Date et heure de début :",
        value = Sys.time() - 3600,  # Par défaut, il y a une heure
        timepicker = TRUE,
        timepickerOpts = list(
          timeFormat = "HH:mm",
          minutesStep = 5
        ),
        language = "fr"
      ),
      airDatepickerInput(
        inputId = "end_datetime",
        label = "Date et heure de fin :",
        value = Sys.time(),
        timepicker = TRUE,
        timepickerOpts = list(
          timeFormat = "HH:mm",
          minutesStep = 5
        ),
        language = "fr"
      ),
      sliderInput("missing_data_threshold", "Seuil de données manquantes (%) :", 
                  min = 0, max = 100, value = 10, step = 1),
      actionButton("generate", "Générer"),
      br(),
      br(),
      h5(textOutput("selected_timestamp")),
      conditionalPanel(
        condition = "output.dataGenerated == true",
        downloadButton("downloadData", "Télécharger les données"),
        br(),
        br(),
        selectInput("station", "Sélectionnez une station :", choices = NULL),
        actionButton("generateGraph", "Générer le graphique"),
        br(),
        br(),
        downloadButton("downloadGraph", "Télécharger le graphique")
      )
    ),
    mainPanel(
      leafletOutput("mymap", height = 600),
      conditionalPanel(
        condition = "output.dataGenerated == true",
        plotOutput("rainPlot", height = 400)
      )
    )
  )
)

server <- function(input, output, session) {

  # Liste des stations
  Station_list <- c('ARCHIOUEST', 'MSE', 'CRBM', 'CEFE', 'CHU1', 'CHU2', 'CHU3',
                    'CHU4', 'CHU5', 'CHU6', 'CHU7', 'CNRS', 'IEM', 'Polytech',
                    'UM', 'UM35', 'Hydropolis', 'RueBrives', 'CINES')

  # Coordonnées du centre de la carte
  x_centre <- 3.85667372
  y_centre <- 43.62999968

  rv <- reactiveValues(
    dataGenerated = FALSE,
    data_file = NULL,
    plotFile = NULL,
    DataP_filtered = NULL
  )

  # Mise à jour de l'heure actuelle
  output$currentTime <- renderText({
    invalidateLater(1000)
    paste("Temps TU :", format(Sys.time(), " %X %a %b %d %Y"))
  })

  output$dataGenerated <- reactive({ rv$dataGenerated })
  outputOptions(output, "dataGenerated", suspendWhenHidden = FALSE)

  # Carte vierge au chargement
  output$mymap <- renderLeaflet({
    leaflet() %>%
      addProviderTiles("OpenStreetMap.DE", options = providerTileOptions(noWrap = TRUE), group = 'OSM') %>%
      setView(lng = x_centre, lat = y_centre, zoom = 11) %>%
      addMeasure(position = "bottomleft",
                 primaryLengthUnit = "meters",
                 primaryAreaUnit = "sqmeters",
                 activeColor = "#3D535D",
                 completedColor = "#7D4479") %>%
      addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>")) %>%
      addLayersControl(
        baseGroups = c("OSM"),
        overlayGroups = c("bulles_pluie", "rasterPluie"),
        options = layersControlOptions(collapsed = FALSE)
      )
  })

  # Action lors du clic sur le bouton "Générer"
  observeEvent(input$generate, {
    req(input$start_datetime, input$end_datetime)

    start_datetime_str <- format(input$start_datetime, "%Y%m%d%H%M")
    end_datetime_str <- format(input$end_datetime, "%Y%m%d%H%M")

    rv$data_file <- paste0("Pluvio_Cumul_Total_", start_datetime_str, "_", end_datetime_str, ".csv")

    if (!file.exists(rv$data_file)) {
      python_command <- paste("python3 generate_cumul_total.py", start_datetime_str, end_datetime_str)
      system(python_command)
    }

    if (!file.exists(rv$data_file)) {
      showNotification("Le fichier de cumul n'a pas pu être généré.", type = "error")
      rv$dataGenerated <- FALSE
      return(NULL)
    }

    DataP <- tryCatch({
      read.csv(rv$data_file, header = TRUE, stringsAsFactors = FALSE)
    }, error = function(e) {
      showNotification(paste("Erreur lors de la lecture du fichier :", e$message), type = "error")
      return(NULL)
    })

    req(DataP)

    DataP$missing_data_percentage <- as.numeric(DataP$missing_data_percentage)

    # Utiliser la valeur du slider
    threshold <- input$missing_data_threshold
    DataP_filtered <- DataP[DataP$missing_data_percentage <= threshold, ]

    if (nrow(DataP_filtered) == 0) {
      showNotification("Aucune station ne respecte le seuil de données manquantes.", type = "error")
      rv$dataGenerated <- FALSE
      return(NULL)
    }

    rv$DataP_filtered <- DataP_filtered

    DataP_filtered$latest_time <- as.POSIXct(DataP_filtered$latest_time, format="%Y-%m-%dT%H:%M:%OS", tz="UTC")

    rv$dataGenerated <- TRUE

    output$selected_timestamp <- renderText({
      paste("Période du", format(input$start_datetime, "%Y-%m-%d %H:%M"),
            "au", format(input$end_datetime, "%Y-%m-%d %H:%M"))
    })

    updateSelectInput(session, "station", choices = DataP_filtered$site)

    # Mise à jour de la carte
    data <- DataP_filtered$total
    datana <- data[data > 0]

    lab <- paste0(
      DataP_filtered$site, " : ", data, " mm",
      "<br />", "Dernière donnée reçue le ", format(DataP_filtered$latest_time, "%Y-%m-%d %H:%M:%S"),
      "<br />", "Données manquantes : ", DataP_filtered$missing_data_percentage, "%"
    )

    couleurs <- colorNumeric("Blues", range(data, na.rm = TRUE), reverse=FALSE)
    max_radius <- 20
    scaled_radius <- sqrt(data) * 4
    scaled_radius[scaled_radius > max_radius] <- max_radius

    non_nul <- sum(data > 0, na.rm = TRUE)

    leafletProxy("mymap") %>%
      clearMarkers() %>%
      clearShapes() %>%
      clearImages() %>%
      clearControls()

    if (non_nul > 1) {
      pts <- data.frame(cumul = data, lon = DataP_filtered$lon, lat = DataP_filtered$lat)
      raindegre <- na.omit(pts)
      coordinates(raindegre) <- ~lon+lat
      crs_obj <- CRS("+init=epsg:4326")

      lon_lim <- c(3.733,3.933)
      lat_lim <- c(43.588,43.690)
      grd <- expand.grid(x = seq(lon_lim[1], lon_lim[2], by = 0.00125),
                         y = seq(lat_lim[1], lat_lim[2], by = 0.00100))
      coordinates(grd) <- ~x + y
      gridded(grd) <- TRUE
      fullgrid(grd) <- TRUE

      idw.res <- idw(formula = cumul ~ 1, locations = raindegre, newdata = grd)
      r <- raster(idw.res)
      proj4string(r) <- crs_obj

      if (file.exists("Masq_pluvio_teletransmis2.csv")) {
        Data_Masque <- read.table("Masq_pluvio_teletransmis2.csv", sep=';', dec=".", header=TRUE)
        coordinates(Data_Masque) <- ~lon+lat
        SpMasque <- SpatialPolygons(list(Polygons(list(Polygon(Data_Masque)), ID = "1")))
        proj4string(SpMasque) <- crs_obj
        r <- mask(r, SpMasque)
      }

      couleurs_raster <- colorNumeric("Blues", values(r), reverse=FALSE, na.color = "transparent")

      leafletProxy("mymap") %>%
        addProviderTiles("OpenStreetMap.DE", options = providerTileOptions(noWrap = TRUE), group = 'OSM') %>%
        setView(lng = x_centre, lat = y_centre, zoom =14 ) %>%
        addMeasure(position = "bottomleft",
                   primaryLengthUnit = "meters",
                   primaryAreaUnit = "sqmeters",
                   activeColor = "#3D535D",
                   completedColor = "#7D4479") %>%
        addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>"), group = 'rasterPluie') %>%
        addRasterImage(r, colors = couleurs_raster, opacity = 0.8, group = 'rasterPluie')  %>%
        addProviderTiles(providers$CartoDB.PositronOnlyLabels, group = 'rasterPluie') %>%
        addMarkers(DataP_filtered$lon, DataP_filtered$lat, icon = makeIcon("www/pluviometre.png", 12, 12),
                   popup = lab, group = 'rasterPluie') %>%
        addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>")) %>%
        addCircleMarkers(DataP_filtered$lon, DataP_filtered$lat, weight = 2,
                         radius = scaled_radius,
                         popup = lapply(lab, HTML),
                         color="black", stroke=TRUE,
                         fillColor = couleurs(data),
                         fillOpacity = 0.7, group = "bulles_pluie") %>%
        addLayersControl(
          baseGroups = c("OSM"),
          overlayGroups = c("bulles_pluie","rasterPluie"),
          options = layersControlOptions(collapsed = FALSE)
        ) %>%
        addLegend(pal = couleurs, values = datana, title = "Pluie mm", opacity = 0.9, group = "bulles_pluie")

    } else if (non_nul == 1) {
      leafletProxy("mymap") %>%
        addProviderTiles("OpenStreetMap.DE", options = providerTileOptions(noWrap = TRUE), group = 'OSM') %>%
        setView(lng = x_centre, lat = y_centre, zoom =14)%>%
        addMeasure(position = "bottomleft",
                   primaryLengthUnit = "meters",
                   primaryAreaUnit = "sqmeters",
                   activeColor = "#3D535D",
                   completedColor = "#7D4479")%>%
        addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>"), group = 'rasterPluie') %>%
        addCircleMarkers(DataP_filtered$lon, DataP_filtered$lat, weight = 2,
                         radius = scaled_radius,
                         popup = lab,
                         color="black", stroke=TRUE,
                         fillColor = "blue",
                         fillOpacity = 0.7, group = 'rasterPluie') %>%
        addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>")) %>%
        addMarkers(DataP_filtered$lon, DataP_filtered$lat, icon = makeIcon("www/pluviometre.png", 12, 12),
                   popup = lab)%>%
        addCircleMarkers(DataP_filtered$lon, DataP_filtered$lat, weight = 2,
                         radius = scaled_radius,
                         popup = lab,
                         color="black", stroke=TRUE,
                         fillColor = "blue",
                         fillOpacity = 0.7, group = "bulles_pluie") %>%
        addLayersControl(
          baseGroups = c("OSM"),
          overlayGroups = c("bulles_pluie","rasterPluie"),
          options = layersControlOptions(collapsed = FALSE)
        )

    } else {
      lab_no_rain <- paste("Pas de pluie au niveau des pluviographes ",
                           "</p>", "<center>", "sur la période sélectionnée", "</center>")
      leafletProxy("mymap") %>%
        addProviderTiles("OpenStreetMap.DE", options = providerTileOptions(noWrap = TRUE)) %>%
        setView(lng = x_centre, lat = y_centre, zoom = 11) %>%
        addMeasure(position = "bottomleft",
                   primaryLengthUnit = "meters",
                   primaryAreaUnit = "sqmeters",
                   activeColor = "#3D535D",
                   completedColor = "#7D4479")%>%
        addTiles(attribution = HTML("<FONT COLOR=black><STRONG>OMSEV Hydrosciences; Projet EVIdENCE</STRONG></FONT>")) %>%
        addMarkers(DataP_filtered$lon, DataP_filtered$lat, icon =  makeIcon("www/pluviometre.png", 12, 12),
                   popup = paste(DataP_filtered$site, " : ", "0.0", "mm"))%>%
        addLabelOnlyMarkers(lng=3.85, lat=43.61,
                            label = lapply(lab_no_rain, HTML),
                            labelOptions = labelOptions(noHide = TRUE, direction = "bottom",
                                                        style = list(
                                                          "color" = "red",
                                                          "font-family" = "serif",
                                                          "font-style" = "italic",
                                                          "font-size" = "14px",
                                                          "border-color" = "rgba(0,0,0,0.5)"
                                                        ))) %>%
        addLayersControl(
          baseGroups = c("OSM"),
          overlayGroups = c("bulles_pluie","rasterPluie"),
          options = layersControlOptions(collapsed = FALSE)
        )
    }
  })

  # Téléchargement des données
  output$downloadData <- downloadHandler(
    filename = function() {
      rv$data_file
    },
    content = function(file) {
      file.copy(rv$data_file, file)
    }
  )

  # Action lors du clic sur le bouton "Générer le graphique"
  observeEvent(input$generateGraph, {
    tryCatch({
      req(rv$dataGenerated)
      req(input$station)
      req(input$start_datetime, input$end_datetime)

      DataP_filtered <- rv$DataP_filtered
      station <- input$station
      start_datetime <- input$start_datetime
      end_datetime <- input$end_datetime

      if (!(station %in% DataP_filtered$site)) {
        showNotification("La station sélectionnée dépasse le seuil de données manquantes.", type = "error")
        return(NULL)
      }

      years <- seq(year(start_datetime), year(end_datetime))
      data_dir <- "/home/ubuntu/gestionpluvio/temp_concat_files/"  # À adapter

      station_data <- data.frame()
      for (y in years) {
        file_path <- file.path(data_dir, paste0(station, "_concatenated_", y, ".csv"))
        if (file.exists(file_path)) {
          temp_data <- read.csv(file_path, stringsAsFactors = FALSE)
          station_data <- rbind(station_data, temp_data)
        }
      }

      if (nrow(station_data) == 0) {
        showNotification("Aucune donnée disponible pour la période sélectionnée.", type = "error")
        return(NULL)
      }

      station_data$Datetime_TU <- as.POSIXct(station_data$Datetime_TU, format="%Y-%m-%d %H:%M:%S", tz = "UTC")
      station_data <- station_data[station_data$Datetime_TU >= start_datetime & station_data$Datetime_TU <= end_datetime, ]

      if (nrow(station_data) == 0) {
        showNotification("Aucune donnée disponible pour la période sélectionnée.", type = "error")
        return(NULL)
      }

      if (any(is.na(station_data$Rain))) {
        total_points <- nrow(station_data)
        missing_points <- sum(is.na(station_data$Rain))
        missing_percentage <- round((missing_points / total_points) * 100, 2)

        showNotification(paste("Des valeurs manquantes détectées pour", station,
                               ":", missing_percentage, "% de données manquantes."), type = "warning")
        station_data$Rain[is.na(station_data$Rain)] <- 0
      }

      station_data$Rain <- as.numeric(station_data$Rain)
      station_data <- station_data %>% arrange(Datetime_TU)
      station_data$Cumul <- cumsum(station_data$Rain)

      range_rain <- range(station_data$Rain, na.rm = TRUE)
      range_cumul <- range(station_data$Cumul, na.rm = TRUE)
      scaling_factor <- diff(range_rain) / diff(range_cumul)
      if (is.infinite(scaling_factor) || is.nan(scaling_factor)) {
        scaling_factor <- 1
      }

      plot_obj <- ggplot(station_data, aes(x = Datetime_TU)) +
        geom_bar(aes(y = Rain), stat = "identity", fill = "blue", width = 60) +
        geom_line(aes(y = Cumul * scaling_factor), color = "red", size = 1) +
        scale_y_continuous(
          name = "Intensité (mm)",
          sec.axis = sec_axis(~ . / scaling_factor, name = "Cumul (mm)")
        ) +
        labs(title = paste("Station :", station), x = "Temps") +
        theme_minimal() +
        theme(
          axis.text.x = element_text(angle = 45, hjust = 1)
        )

      output$rainPlot <- renderPlot({
        plot_obj
      })

      tempPlotFile <- tempfile(fileext = ".png")
      ggsave(filename = tempPlotFile, plot = plot_obj, width = 12, height = 8, units = "in")
      rv$plotFile <- tempPlotFile

    }, error = function(e) {
      showNotification(paste("Une erreur est survenue :", e$message), type = "error")
    })
  })

  # Handler pour le bouton de téléchargement du graphique
  output$downloadGraph <- downloadHandler(
    filename = function() {
      paste0("Graph_", input$station, "_", format(input$start_datetime, "%Y%m%d%H%M"), "_", format(input$end_datetime, "%Y%m%d%H%M"), ".png")
    },
    content = function(file) {
      file.copy(rv$plotFile, file)
    }
  )
}

shinyApp(ui, server)

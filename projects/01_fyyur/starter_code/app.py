#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import config
import json
import dateutil.parser
from datetime import datetime
import babel
import psycopg2
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import func
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    __searchable__ = ["name","city","state","address"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_description = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)

    shows = db.relationship('Show', backref = 'venue')
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'
    __searchable__ = ["name","city","state","address"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean, default=False)
    website = db.Column(db.String())
  
    shows = db.relationship('Show', backref= 'artist')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
    __tablename__ ='Show'
  
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, primary_key=True)
        
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  areas = Venue.query.distinct('city','state').all()

  today = datetime.now()
  today = today.strftime('%Y-%m-%d')

  def get_venue(venue):
      venue_id = Venue.id 
      upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
      Show.start_time>today).all()
  
      upcoming_shows_count = 0
      for show in upcoming_shows:
          upcoming_shows_count = upcoming_shows_count+1
      return {'id': venue_id, 'name': venue.name, 'num_upcoming_shows': upcoming_shows_count}

  for area in areas:
      venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
      record = {
          'city': area.city,
          'state': area.state,
          'venues': [get_venue(venue) for venue in venues],
      }
      data.append(record)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  search_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  count_results = len(search_results)
  response = {}
  data = []

  today = datetime.now()
  today = today.strftime('%Y-%m-%d')
  def get_upcoming_number(venue_id):
      total = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
      Show.start_time>today).all()
      return len(total)
  for result in search_results:
      data.append({
          "id": result.id,
          "name": result.name,
          "num_upcoming_shows": get_upcoming_number(result.id)
      })
  response["count"] = count_results
  response["data"] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    arr = venue.genres[1:-1] 
    arr = ''.join(arr).split(",")
    venue.genres = arr
    today = datetime.now()
    today = today.strftime('%Y-%m-%d')
    if venue.seeking_description:
        venue.seeking_text = "We are on the lookout for a local artist to play every two weeks. Please call us."
  

    upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
        Show.start_time>today).all()
    past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
        Show.start_time<today).all()
 
    def shows(shows):
        show_render_data = []
        shows_count = 0
        for show in shows:
            shows_count = shows_count+1
            show_render_data.append({
                "start_time" : show.start_time,
                "artist_id" : show.artist_id,
                "artist_image_link" : show.artist.image_link,
                "artist_name" : show.artist.name
            })
        return [shows_count, show_render_data]

    past_shows = shows(past_shows)
    upcoming_shows = shows(upcoming_shows)

    venue.past_shows_count = past_shows[0]
    venue.past_shows = past_shows[1]

    venue.upcoming_shows_count = upcoming_shows[0]
    venue.upcoming_shows = upcoming_shows[1]
    return render_template('pages/show_venue.html', venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
  
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    error = False
    try:
        venue=Venue.query.get(venue_id)
        venue.name=form.name.data,
        venue.genres=form.genres.data,
        venue.city=form.city.data,
        venue.state=form.state.data,
        venue.phone=form.phone.data,
        venue.address=form.address.data,
        venue.facebook_link=form.facebook_link.data,
        venue.image_link=form.image_link.data

        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue not updated')
        else:
            flash('Venue ' + form.name.data + ' was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
      new_venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
      )
      db.session.add(new_venue)
      db.session.commit()
  except :
      db.session.rollback()
      error = True
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      else:
          flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')
  
    return render_template('pages/venues.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    search_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    count_results = len(search_results)
    response = {}
    data = []

    today = datetime.now()
    today = today.strftime('%Y-%m-%d')

    def get_upcoming_number(artist_id):
        total = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time>today).all()
        return len(total)
    for result in search_results:
        data.append({
            'id': result.id,
            'name': result.name,
            'num_upcoming_shows': get_upcoming_number(result.id)
        })
    response['count'] = count_results
    response['data'] = data

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    arr = artist.genres[1:-1] 
    arr = ''.join(arr).split(",")
    artist.genres = arr
    today = datetime.now()
    today = today.strftime('%Y-%m-%d')
    if artist.seeking_venue:
        artist.seeking_text = "Looking for venue to play in."
  
    upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time>today).all()
    past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time<today).all()

    def shows(shows):
        show_render_data = []
        shows_count = 0
        for show in shows:
            shows_count = shows_count+1
            show_render_data.append({
                "start_time" : show.start_time,
                "venue_id" : show.venue_id,
                "venue_image_link" : show.venue.image_link,
                "venue_name" : show.venue.name
            })
        return [shows_count, show_render_data]

    past_shows = shows(past_shows)
    upcoming_shows = shows(upcoming_shows)

    artist.past_shows_count = past_shows[0]
    artist.past_shows = past_shows[1]

    artist.upcoming_shows_count = upcoming_shows[0]
    artist.upcoming_shows = upcoming_shows[1]

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist=Artist.query.get(artist_id)
  
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    error = False
    try:
        artist=Artist.query.get(artist_id)
        artist.name=form.name.data,
        artist.genres=form.genres.data,
        artist.city=form.city.data,
        artist.state=form.state.data,
        artist.phone=form.phone.data,
        artist.facebook_link=form.facebook_link.data,
        artist.image_link=form.image_link.data

        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Artist not updated')
        else:
            flash('Artist ' + form.name.data + ' was successfully updated!')
    
    return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        new_artist = Artist(
          	name = request.form['name'],
          	city = request.form['city'],
          	state = request.form['state'],
          	genres = request.form.getlist('genres'),
          	facebook_link = request.form['facebook_link'],
          	website = request.form['website'],
        	  image_link = request.form['image_link']
        )
      
        db.session.add(new_artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())   
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
    
    return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')
  
    return render_template('pages/artists.html')
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

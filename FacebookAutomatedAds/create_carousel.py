from facebookads.adobjects.adcreativelinkdatacalltoactionvalue import AdCreativeLinkDataCallToActionValue
from facebookads.adobjects.adcreativelinkdatachildattachment import AdCreativeLinkDataChildAttachment
from facebookads.adobjects.adcreativelinkdatacalltoaction import AdCreativeLinkDataCallToAction
from facebookads.adobjects.adcreativeobjectstoryspec import AdCreativeObjectStorySpec
from facebookads.adobjects.adcreativelinkdata import AdCreativeLinkData
from facebookads.objects import Ad
from facebookads.adobjects.campaign import Campaign
from facebookads.adobjects.adcreative import AdCreative
from facebookads.adobjects.adcreativeobjectstoryspec import AdCreativeObjectStorySpec
from time import sleep
import header
import my_constants as constants
import json
import psycopg2
import psycopg2.extras
import image_hash
import sys
import urlparse
from facebookads import exceptions
import logging
from datetime import date

def create_carousel_ad(caption,adset_id,ad_name,times,design_list,account_id,land_on_design,url,campaign_tag):
	logger = logging.getLogger('testlogger')
	logger.debug("In create carousel")
	conn = None
	simple_list=[]
	account_medium_list={"act_940036526039709":"fb_ocpc","act_938286879548007":"acpm","act_1010404049002956":"acpm","act_1385041538425866":"acpm","act_1128744890502204":"jcpc","act_10152414205523137":"int","act_972844956092199":"exp"}
	utm_medium=account_medium_list[account_id]
	try:
		urlparse.uses_netloc.append("postgres")
		database_url = urlparse.urlparse(constants.database_url)
		conn = psycopg2.connect( database=database_url.path[1:], user=database_url.username, password=database_url.password, host=database_url.hostname, port=database_url.port )
		curr = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		for i in xrange(times):
			design_id=design_list[i]
			curr.execute('SELECT discount_percent,designer_id from designs where id='+str(design_id))
			row=curr.fetchone()
			curr.execute('SELECT id,photo_file_name FROM images where design_id = '+str(design_id))
			rows=curr.fetchone()
			curr.execute('SELECT name FROM "categories" INNER JOIN "categories_designs" ON "categories"."id" = "categories_designs"."category_id" WHERE design_id ='+str(design_id))
			category_name = curr.fetchone()
			image_link = image_hash.get_image_link(rows['photo_file_name'],rows['id'])
			if row['discount_percent'] is None:
				row['discount_percent']=0
			product1 = AdCreativeLinkDataChildAttachment()
			if land_on_design:
				product1[AdCreativeLinkDataChildAttachment.Field.link] = 'www.mirraw.com/designers/'+str(row['designer_id'])+'/designs/'+str(design_id)+'?utm_source=facebook-auto&utm_medium='+utm_medium+'&utm_campaign='+campaign_tag
			else:
				product1[AdCreativeLinkDataChildAttachment.Field.link] = url+'?pid='+str(design_id)+'&utm_source=facebook&utm_medium='+utm_medium+'&utm_campaign='+campaign_tag
			product1[AdCreativeLinkDataChildAttachment.Field.name] = category_name['name']
			action = AdCreativeLinkDataCallToAction()
			link_value = AdCreativeLinkDataCallToActionValue()
			link_value[AdCreativeLinkDataCallToActionValue.Field.link_title] = 'Discount '+str(row['discount_percent'])+'%'
			action[AdCreativeLinkDataCallToAction.Field.type] = AdCreativeLinkDataCallToAction.Type.shop_now
			action[AdCreativeLinkDataCallToAction.Field.value] = link_value
			product1[AdCreativeLinkDataChildAttachment.Field.call_to_action] = action
			product1[AdCreativeLinkDataChildAttachment.Field.description] = 'Discount '+str(row['discount_percent'])+'%'
			product1[AdCreativeLinkDataChildAttachment.Field.image_hash] = image_hash.get_image_hash(image_link,rows[1],account_id)
			sleep(0.5)
			simple_list.append(product1)

		link = AdCreativeLinkData()
		link[link.Field.link] = url+'&utm_source=facebook&utm_medium='+utm_medium+'&utm_campaign='+campaign_tag
		link[link.Field.child_attachments] = simple_list
		link[link.Field.caption] = url+'&utm_source=facebook&utm_medium='+utm_medium+'&utm_campaign='+campaign_tag
		call_to_action_button = AdCreativeLinkDataCallToAction()
		call_to_action_button[AdCreativeLinkDataCallToAction.Field.type]=AdCreativeLinkDataCallToAction.Type.shop_now
		link[link.Field.call_to_action] = call_to_action_button
		link[link.Field.message] = caption

		logger.info(link)
		story = AdCreativeObjectStorySpec()
		story[story.Field.page_id] = constants.page_id
		story[story.Field.link_data] = link

		creative = AdCreative(parent_id=account_id)
		creative[AdCreative.Field.name] = 'MPA Creative'
		creative[AdCreative.Field.object_story_spec] = story
		creative.remote_create()
		creative=json.loads(str(creative).replace('<AdCreative> ',''))

		logger.info(creative)
		ad = Ad(parent_id=account_id)
		ad[Ad.Field.name] = ad_name
		ad[Ad.Field.adset_id] = adset_id
		ad[Ad.Field.status] = Campaign.Status.paused
		ad[Ad.Field.creative] = {'creative_id': str(creative['id'])}
		logger.info('Creating Ad')
		ad.remote_create()
		logger.info(ad)

	except psycopg2.DatabaseError, e:
		logger.error('Error %s' % e)
		return False

	except exceptions.FacebookError, e:
		logger.error('Error %s' % e)
		return False

	finally:
		if conn:
			conn.close()
	return True
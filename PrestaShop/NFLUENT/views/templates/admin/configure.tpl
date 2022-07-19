{*
* 2007-2022 PrestaShop
*
* NOTICE OF LICENSE
*
* This source file is subject to the Academic Free License (AFL 3.0)
* that is bundled with this package in the file LICENSE.txt.
* It is also available through the world-wide-web at this URL:
* http://opensource.org/licenses/afl-3.0.php
* If you did not receive a copy of the license and are unable to
* obtain it through the world-wide-web, please send an email
* to license@prestashop.com so we can send you a copy immediately.
*
* DISCLAIMER
*
* Do not edit or add to this file if you wish to upgrade PrestaShop to newer
* versions in the future. If you wish to customize PrestaShop for your
* needs please refer to http://www.prestashop.com for more information.
*
*  @author    PrestaShop SA <contact@prestashop.com>
*  @copyright 2007-2022 PrestaShop SA
*  @license   http://opensource.org/licenses/afl-3.0.php  Academic Free License (AFL 3.0)
*  International Registered Trademark & Property of PrestaShop SA
*}

<div class="panel">
	<div class="row moduleconfig-header">
		<div class="col-xs-5 text-right">
			<img src="{$module_dir|escape:'html':'UTF-8'}views/img/logo-nfluent-purple.svg" />
		</div>
		<div class="col-xs-7 text-left">
			<h2>{l s='NFT' mod='NFLUENT'}</h2>
			<h4>{l s='Vendez des NFTs depuis votre boutique Prestashop' mod='NFLUENT'}</h4>
		</div>
	</div>

	<hr />

	<div class="moduleconfig-content">
		<div class="row">
			<div class="col-xs-12">
				<p>
					<h4>{l s='Serveur NFLUENT' mod='NFLUENT'}</h4>
{*					<ul class="ul-spaced">*}
{*						<li><strong>{l s='Lorem ipsum dolor sit amet' mod='NFLUENT'}</strong></li>*}
{*						<li>{l s='Lorem ipsum dolor sit amet' mod='NFLUENT'}</li>*}
{*						<li>{l s='Lorem ipsum dolor sit amet' mod='NFLUENT'}</li>*}
{*						<li>{l s='Lorem ipsum dolor sit amet' mod='NFLUENT'}</li>*}
{*						<li>{l s='Lorem ipsum dolor sit amet' mod='NFLUENT'}</li>*}
{*					</ul>*}

        <div class="form-group">
          <form action="ServerConfigForm?action=submit" method="post">
            <table style="width: 100%;">
              <tr>
                <td>
                  <label class="control-label col-lg-4 required">Server address:</label>
                </td>
                <td>
                  <input type="text" name="SERVER_ADDR" id="SERVER_ADDR" size="40" value="https://server.f80lab.com:4242">
                </td>
                <td>
                  <input class="btn btn-default" type="submit" value="Save">
                </td>
              </tr>
            </table>
          </form>
        </div>


				</p>

				<br />

				<p class="text-center">
					<strong>
						<a href="https://tokenfactory.nfluent.io" target="TokenFactory" title="Token Factory">
							{l s='Token Factory' mod='NFLUENT' }
						</a>
					</strong>
				</p>
			</div>
		</div>
	</div>
</div>

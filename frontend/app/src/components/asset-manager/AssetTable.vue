<template>
  <card outlined-body>
    <template #title>
      {{ $t('asset_table.assets') }}
    </template>
    <template #subtitle>
      {{ $t('asset_table.subtitle') }}
    </template>
    <template #search>
      <v-row justify="end" no-gutters>
        <v-col cols="12" sm="4">
          <v-text-field
            :value="pendingSearch"
            dense
            prepend-inner-icon="mdi-magnify"
            :label="$t('asset_table.search')"
            outlined
            @input="onSearchTermChange($event)"
          />
        </v-col>
      </v-row>
    </template>
    <v-btn absolute fab top right dark color="primary" @click="add">
      <v-icon> mdi-plus </v-icon>
    </v-btn>
    <data-table
      :items="tokens"
      :loading="loading"
      :headers="headers"
      single-expand
      :expanded="expanded"
      item-key="identifier"
      sort-by="name"
      :search.sync="search"
    >
      <template #item.name="{ item }">
        <asset-details-base
          :changeable="change"
          opens-details
          :asset="getAsset(item)"
        />
      </template>
      <template #item.address="{ item }">
        <hash-link v-if="item.address" :text="item.address" />
      </template>
      <template #item.started="{ item }">
        <date-display v-if="item.started" :timestamp="item.started" />
        <span v-else>-</span>
      </template>
      <template #item.assetType="{ item }">
        {{ capitalize(item.assetType) }}
      </template>
      <template #item.actions="{ item }">
        <row-actions
          :edit-tooltip="$t('asset_table.edit_tooltip')"
          :delete-tooltip="$t('asset_table.delete_tooltip')"
          @edit-click="edit(item)"
          @delete-click="deleteAsset(item)"
        />
      </template>
      <template #expanded-item="{ item, headers }">
        <table-expand-container
          visible
          :colspan="headers.length"
          :padded="false"
        >
          <template #title>
            {{ $t('asset_table.underlying_tokens') }}
          </template>
          <v-simple-table>
            <thead>
              <tr>
                <th>{{ $t('underlying_token_manager.tokens.address') }}</th>
                <th>{{ $t('underlying_token_manager.tokens.weight') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="token in item.underlyingTokens" :key="token.address">
                <td class="grow">
                  <hash-link :text="token.address" full-address />
                </td>
                <td class="shrink">
                  {{
                    $t('underlying_token_manager.tokens.weight_percentage', {
                      weight: token.weight
                    })
                  }}
                </td>
              </tr>
            </tbody>
          </v-simple-table>
        </table-expand-container>
      </template>
      <template #item.expand="{ item }">
        <row-expander
          v-if="item.underlyingTokens && item.underlyingTokens.length > 0"
          :expanded="expanded.includes(item)"
          @click="expanded = expanded.includes(item) ? [] : [item]"
        />
      </template>
    </data-table>
  </card>
</template>

<script lang="ts">
import { Component, Emit, Prop, Vue } from 'vue-property-decorator';
import { DataTableHeader } from 'vuetify';
import { ManagedAsset } from '@/components/asset-manager/types';
import AssetDetailsBase from '@/components/helper/AssetDetailsBase.vue';
import DataTable from '@/components/helper/DataTable.vue';
import RowActions from '@/components/helper/RowActions.vue';
import RowExpander from '@/components/helper/RowExpander.vue';
import TableExpandContainer from '@/components/helper/table/TableExpandContainer.vue';
import { capitalize } from '@/filters';
import { EthereumToken } from '@/services/assets/types';

@Component({
  components: {
    DataTable,
    TableExpandContainer,
    RowActions,
    RowExpander,
    AssetDetailsBase
  }
})
export default class AssetTable extends Vue {
  @Prop({ required: true, type: Array })
  tokens!: ManagedAsset[];
  @Prop({ required: false, type: Boolean, default: false })
  loading!: string;
  @Prop({ required: true, type: Boolean })
  change!: boolean;

  @Emit()
  add() {}
  @Emit()
  edit(_asset: ManagedAsset) {}
  @Emit()
  deleteAsset(_asset: ManagedAsset) {}

  expanded = [];
  search: string = '';
  pendingSearch: string = '';
  searchTimeout: any = null;

  onSearchTermChange(term: string) {
    this.pendingSearch = term;
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = null;
    }
    this.searchTimeout = setTimeout(
      () => (this.search = this.pendingSearch),
      400
    );
  }

  readonly headers: DataTableHeader[] = [
    {
      text: this.$t('asset_table.headers.asset').toString(),
      value: 'name'
    },
    {
      text: this.$t('asset_table.headers.type').toString(),
      value: 'assetType'
    },
    {
      text: this.$t('asset_table.headers.address').toString(),
      value: 'address'
    },
    {
      text: this.$t('asset_table.headers.started').toString(),
      value: 'started'
    },
    {
      text: '',
      value: 'actions'
    },
    {
      text: '',
      width: '48px',
      value: 'expand'
    }
  ];

  capitalize(string?: string) {
    return capitalize(string ?? 'ethereum token');
  }

  getAsset(item: EthereumToken) {
    const name =
      item.name ?? item.symbol ?? item.identifier?.replace('_ceth_', '');
    return {
      name,
      symbol: item.symbol ?? '',
      identifier: item.identifier
    };
  }
}
</script>

<style scoped lang="scss"></style>

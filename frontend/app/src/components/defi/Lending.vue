<template>
  <progress-screen v-if="loading">
    <template #message>{{ $t('lending.loading') }}</template>
  </progress-screen>
  <v-container v-else>
    <v-row no-gutters>
      <v-col>
        <refresh-header
          :loading="anyRefreshing"
          :title="$t('lending.title')"
          @refresh="refresh()"
        >
          <confirmable-reset
            v-if="!premium"
            :loading="anyRefreshing"
            :tooltip="$t('lending.reset_tooltip')"
            :disabled="resetSelection.length === 0"
            @reset="reset()"
          >
            {{ $t('lending.reset_confirm') }}
            <div />
            <v-row>
              <v-col class="text-center font-weight-medium">
                {{ $t('lending.reset.protocol_selection') }}
              </v-col>
            </v-row>
            <v-row align="center" justify="center">
              <v-col cols="auto">
                <v-btn-toggle v-model="resetSelection" multiple>
                  <v-btn icon :value="AAVE">
                    <defi-protocol-icon mode="icon" :protocol="AAVE" />
                  </v-btn>
                  <v-btn icon :value="YEARN_VAULTS">
                    <defi-protocol-icon mode="icon" :protocol="YEARN_VAULTS" />
                  </v-btn>
                </v-btn-toggle>
              </v-col>
            </v-row>
          </confirmable-reset>
        </refresh-header>
      </v-col>
    </v-row>
    <v-row class="mt-8" no-gutters>
      <v-col cols="12">
        <stat-card-wide :cols="3">
          <template #first-col>
            <stat-card-column>
              <template #title>
                {{ $t('lending.currently_deposited') }}
              </template>
              <amount-display
                :value="
                  totalLendingDeposit(selectedProtocols, selectedAddresses)
                "
                fiat-currency="USD"
                show-currency="symbol"
              />
            </stat-card-column>
          </template>
          <template #second-col>
            <stat-card-column>
              <template #title>
                {{ $t('lending.effective_interest_rate') }}
                <v-tooltip bottom max-width="300px">
                  <template #activator="{ on }">
                    <v-icon small class="mb-3 ml-1" v-on="on">
                      mdi-information
                    </v-icon>
                  </template>
                  <div>{{ $t('lending.effective_interest_rate_tooltip') }}</div>
                </v-tooltip>
              </template>
              <percentage-display
                justify="start"
                :value="
                  effectiveInterestRate(selectedProtocols, selectedAddresses)
                "
              />
            </stat-card-column>
          </template>
          <template #third-col>
            <stat-card-column lock>
              <template #title>
                {{ $t('lending.profit_earned') }}
                <premium-lock v-if="!premium" class="d-inline" />
              </template>
              <amount-display
                v-if="!premium"
                :loading="secondaryLoading"
                :value="totalUsdEarned(selectedProtocols, selectedAddresses)"
                show-currency="symbol"
                fiat-currency="USD"
              />
            </stat-card-column>
          </template>
        </stat-card-wide>
      </v-col>
    </v-row>
    <v-row class="mt-8" no-gutters>
      <v-col cols="12" sm="6" class="pe-sm-4">
        <blockchain-account-selector
          v-model="selectedAccount"
          hint
          :chains="['ETH']"
          :usable-accounts="defiAccounts(selectedProtocols)"
        />
      </v-col>
      <v-col cols="12" sm="6" class="ps-sm-4 pt-4 pt-sm-0">
        <defi-protocol-selector v-model="protocol" />
      </v-col>
    </v-row>
    <v-row v-if="!isYearnVaults" class="mt-8" no-gutters>
      <v-col>
        <stat-card :title="$t('lending.assets')">
          <lending-asset-table
            :loading="refreshing"
            :assets="
              aggregatedLendingBalances(selectedProtocols, selectedAddresses)
            "
          />
        </stat-card>
      </v-col>
    </v-row>
    <v-row
      v-if="isYearnVaults || selectedProtocols.length === 0"
      class="mt-8"
      no-gutters
    >
      <v-col>
        <yearn-assets-table
          :loading="refreshing"
          :selected-addresses="selectedAddresses"
        />
      </v-col>
    </v-row>
    <compound-lending-details
      v-if="premium && isCompound"
      class="mt-8"
      :addresses="selectedAddresses"
    />
    <yearn-vaults-profit-details
      v-if="premium && (isYearnVaults || selectedProtocols.length === 0)"
      class="mt-8"
      :profit="yearnVaultsProfit(selectedAddresses)"
    />
    <aave-earned-details
      v-if="premium && (isAave || selectedProtocols.length === 0)"
      class="mt-8"
      :profit="aaveTotalEarned(selectedAddresses)"
    />
    <v-row class="loans__history mt-8" no-gutters>
      <v-col cols="12">
        <premium-card v-if="!premium" :title="$t('lending.history')" />
        <lending-history
          v-else
          :loading="secondaryRefreshing"
          :history="lendingHistory(selectedProtocols, selectedAddresses)"
          :floating-precision="floatingPrecision"
          @open-link="openLink($event)"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { default as BigNumber } from 'bignumber.js';
import Component from 'vue-class-component';
import { Mixins } from 'vue-property-decorator';
import { mapActions, mapGetters, mapState } from 'vuex';
import LendingAssetTable from '@/components/defi/display/LendingAssetTable.vue';
import YearnAssetsTable from '@/components/defi/yearn/YearnAssetsTable.vue';
import AmountDisplay from '@/components/display/AmountDisplay.vue';
import PercentageDisplay from '@/components/display/PercentageDisplay.vue';
import PremiumCard from '@/components/display/PremiumCard.vue';
import StatCard from '@/components/display/StatCard.vue';
import StatCardColumn from '@/components/display/StatCardColumn.vue';
import StatCardWide from '@/components/display/StatCardWide.vue';
import BlockchainAccountSelector from '@/components/helper/BlockchainAccountSelector.vue';
import ConfirmableReset from '@/components/helper/ConfirmableReset.vue';
import DefiProtocolSelector from '@/components/helper/DefiProtocolSelector.vue';
import PremiumLock from '@/components/helper/PremiumLock.vue';
import ProgressScreen from '@/components/helper/ProgressScreen.vue';
import RefreshHeader from '@/components/helper/RefreshHeader.vue';
import StatusMixin from '@/mixins/status-mixin';
import {
  AaveEarnedDetails,
  CompoundLendingDetails,
  LendingHistory,
  YearnVaultsProfitDetails
} from '@/premium/premium';
import {
  DEFI_AAVE,
  DEFI_COMPOUND,
  DEFI_PROTOCOLS,
  DEFI_YEARN_VAULTS
} from '@/services/defi/consts';
import { SupportedDefiProtocols } from '@/services/defi/types';
import { YearnVaultProfitLoss } from '@/services/defi/types/yearn';
import { Section } from '@/store/const';
import { BaseDefiBalance, ProfitLossModel } from '@/store/defi/types';
import { Account, DefiAccount } from '@/typing/types';

@Component({
  components: {
    YearnAssetsTable,
    PercentageDisplay,
    CompoundLendingDetails,
    YearnVaultsProfitDetails,
    ConfirmableReset,
    RefreshHeader,
    LendingAssetTable,
    DefiProtocolSelector,
    StatCardColumn,
    AmountDisplay,
    PremiumCard,
    BlockchainAccountSelector,
    StatCard,
    StatCardWide,
    ProgressScreen,
    PremiumLock,
    AaveEarnedDetails,
    LendingHistory
  },
  computed: {
    ...mapState('session', ['premium']),
    ...mapGetters('session', ['floatingPrecision']),
    ...mapGetters('defi', [
      'totalUsdEarned',
      'totalLendingDeposit',
      'defiAccounts',
      'effectiveInterestRate',
      'aggregatedLendingBalances',
      'lendingHistory',
      'yearnVaultsProfit',
      'aaveTotalEarned'
    ])
  },
  methods: {
    ...mapActions('defi', ['fetchLending', 'resetDB'])
  }
})
export default class Lending extends Mixins(StatusMixin) {
  premium!: boolean;
  floatingPrecision!: number;
  selectedAccount: Account | null = null;
  totalLendingDeposit!: (
    protocols: SupportedDefiProtocols[],
    addresses: string[]
  ) => BigNumber;
  defiAccounts!: (protocols: SupportedDefiProtocols[]) => DefiAccount[];
  aggregatedLendingBalances!: (
    protocols: SupportedDefiProtocols[],
    addresses: string[]
  ) => BaseDefiBalance[];
  effectiveInterestRate!: (
    protocols: SupportedDefiProtocols[],
    addresses: string[]
  ) => string;
  protocol: SupportedDefiProtocols | null = null;
  fetchLending!: (refresh?: boolean) => Promise<void>;
  resetDB!: (protocols: SupportedDefiProtocols[]) => Promise<void>;
  totalUsdEarned!: (
    protocols: SupportedDefiProtocols[],
    addresses: string[]
  ) => BigNumber;
  yearnVaultsProfit!: (addresses: string[]) => YearnVaultProfitLoss[];
  aaveTotalEarned!: (addresses: string[]) => ProfitLossModel[];

  section = Section.DEFI_LENDING;
  secondSection = Section.DEFI_LENDING_HISTORY;

  resetSelection: SupportedDefiProtocols[] = [];

  readonly AAVE = DEFI_AAVE;
  readonly YEARN_VAULTS = DEFI_YEARN_VAULTS;

  get selectedAddresses(): string[] {
    return this.selectedAccount ? [this.selectedAccount.address] : [];
  }

  get defiAddresses(): string[] {
    return this.defiAccounts(this.selectedProtocols).map(
      ({ address }) => address
    );
  }

  get isCompound(): boolean {
    return (
      this.selectedProtocols.length === 1 &&
      this.selectedProtocols.includes(DEFI_COMPOUND)
    );
  }

  get isYearnVaults(): boolean {
    return (
      this.selectedProtocols.length === 1 &&
      this.selectedProtocols.includes(DEFI_YEARN_VAULTS)
    );
  }

  get isAave(): boolean {
    return (
      this.selectedProtocols.length === 1 &&
      this.selectedProtocols.includes(DEFI_AAVE)
    );
  }

  async refresh() {
    await this.fetchLending(true);
  }

  async reset() {
    await this.resetDB(this.resetSelection);
  }

  async created() {
    const queryElement = this.$route.query['protocol'];
    const protocolIndex = DEFI_PROTOCOLS.findIndex(
      protocol => protocol === queryElement
    );
    if (protocolIndex >= 0) {
      this.protocol = DEFI_PROTOCOLS[protocolIndex];
    }
    await this.fetchLending();
  }

  get selectedProtocols(): SupportedDefiProtocols[] {
    return this.protocol ? [this.protocol] : [];
  }

  openLink(url: string) {
    this.$interop.openUrl(url);
  }
}
</script>
